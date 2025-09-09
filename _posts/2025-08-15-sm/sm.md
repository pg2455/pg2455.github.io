---
layout: distillPost
title:  Forwards and Backprop through Online Attention
date: 2025-09-09
description: 

_styles: >
 h3, h2, h1 {
   padding-top: 0!important;
 }

distill: true
mathjax: true
bibliography: llm.bib
---

**What is Attention?**
At a high level, attention ([Vaswani et al.](https://arxiv.org/abs/1706.03762)<d-cite key="vaswani2017attention"></d-cite>) is a mechanism that allows a neural network to focus on the most relevant pieces of information when making a decision. Instead of treating all input tokens (words, pixels, etc.) equally, it learns to weigh them differently depending on the current context.

A useful way to think of it:

* The network first maps the input into a high-dimensional space — a kind of *library of representations*.
* Then, when the model needs to produce an output (like predicting the next word), attention acts like a search engine inside the model. It asks: *“Given the current context, which entries in this library are most useful right now?”*
* The result is a weighted combination of those entries, so the model doesn’t just recall one thing, but blends together the most relevant information for the task at hand.

<div style="background-color: rgba(245, 245, 204, 0.5); padding: 10px; border-radius: 8px; border: 1px solid #e0e0b0;">
Attention has been the engine behind much of the progress in LLMs. But the mechanism comes with a cost: **computing attention in the straightforward way requires quadratic time and memory in the sequence length**. As models stretch into contexts of tens or even hundreds of thousands of tokens, this quadratic blow-up quickly becomes the bottleneck.

Early research explored many clever approximations, such as low-rank projections, kernel tricks, sparsity patterns, but most came with a trade-off: efficiency at the cost of exactness.

**What’s remarkable is that the most effective solution turned out to be almost trivial: compute attention online, piece by piece, without ever materializing the full attention matrix.**


In this post, we’ll unpack what that means, why it works, and how both the forward and backward passes of attention can be carried out in a streaming fashion. 
To avoid the memory overhead of storing large intermediate structures (like the full score matrix), we’ll also show how to derive gradients through attention online: processing only small chunks of keys, values, and queries at a time.

</div>
<br>

I’ll use code examples throughout to make these ideas concrete.

Much of this discussion is inspired by the appendices of [FlashAttention](https://github.com/Dao-AILab/flash-attention)<d-cite key="dao2022flashattention"></d-cite>, which achieves single-GPU efficiency by fusing operations and carefully managing memory, and by [RingAttention](https://arxiv.org/abs/2310.01889)<d-cite key="liu2023ring"></d-cite>, which extends the same principle across GPUs by overlapping partial computations with communication of keys and values.

## Forward Pass (Full Attention)

We start with three matrices:

* **Queries** \\( Q \in \mathbb{R}^{N \times d} \\)
* **Keys** \\( K \in \mathbb{R}^{M \times d} \\)
* **Values** \\( V \in \mathbb{R}^{M \times d} \\)

Here, \\( d \\) is the hidden dimension, \\( N \\) is the number of query tokens, and \\( M \\) is the number of key/value tokens.

The attention output is defined as:

\\[
\text{Attn}(Q, K, V) = \text{Softmax}(\tau QK^\top) V
\\]

where \\( \tau = \frac{1}{\sqrt{d}} \\) is a scaling factor to keep dot products numerically stable.

Breaking it down step by step:

**Similarity scores:**

   \\[
   S = QK^\top
   \\]

   Each entry \\( S_{ij} \\) measures how much query \\( i \\) attends to key \\( j \\).

**Attention weights:**

   \\[
   P = \text{Softmax}(\tau S)
   \\]

   The softmax turns raw scores into probabilities, so each query distributes its attention across all keys.

**Weighted aggregation:**

   \\[
   O = PV
   \\]

   Finally, each query’s output is a weighted sum of the values, with weights given by \\( P \\).



In the code block below, we’ll manually implement the attention output as `O_manual` and verify that it matches PyTorch’s built-in result `O`.


```python
B = 10
L = 20
D = 16
Q = torch.randn(B, L, D, requires_grad=True)
K = torch.randn(B, L, D, requires_grad=True)
V = torch.randn(B, L, D, requires_grad=True)

tau = 1. / math.sqrt(D)

# Using PyTorch Module
# API expects [B, heads, L, D]; here head dim = 1
O = F.scaled_dot_product_attention(Q.unsqueeze(1), K.unsqueeze(1), V.unsqueeze(1))
O = O.squeeze(1)

# Handcoded batch attention
scores = tau * torch.matmul(Q, K.transpose(-2, -1))
sm = torch.softmax(scores, dim=-1)
O_manual = torch.matmul(sm, V)

print("O == O_manual: ", torch.allclose(O, O_manual, atol=1e-6))

```

    O == O_manual:  True


## Numerically Stable Forward Pass (Full Attention)

So far, we assumed the entire \\( Q, K, V \\) matrices fit in memory at once. But in practice, this isn’t always possible:

* On a single GPU, **memory constraints** motivate algorithms like *FlashAttention*, which compute attention block by block.
* In distributed settings, **hardware memory limits** across devices motivate approaches like *RingAttention*, which stream keys and values across GPUs while overlapping computation with communication.

The attention computation can be written elementwise as:

\\[
S_{ij} = Q_i^\top K_j
\\]

\\[
P_{ij} = \frac{\exp(\tau S_{ij})}{\sum_{j}\exp(\tau S_{ij})}
\\]

\\[
O_{i,:} = \sum_{j} P_{ij} \, V_{j,:}
\\]

Combining the steps, each output row can be expressed directly as:

\\[
O_{i,:} = \frac{\sum_{j}\exp\big(\tau Q_i^\top K_j\big)\, V_{j,:}}{\sum_{j}\exp\!\big(\tau Q_i^\top K_j\big)}
\\]

Directly exponentiating large dot products can cause overflow. To prevent this, we apply the classic log-sum-exp trick, subtracting the maximum score before exponentiation:

\\[
m_i = \max_j \, Q_i^\top K_j
\\]

\\[
O_{i,:} = \frac{\sum_{j}\exp\big(\tau Q_i^\top K_j - m_i\big)\, V_{j,:}}{\sum_{j}\exp\big(\tau Q_i^\top K_j - m_i\big)}
\\]

> This normalization step keeps the computation stable and memory-efficient.

In the code block below, we’ll manually implement the normalized attention output as `O_m_with_max` and verify that it matches PyTorch’s built-in result `O`.


```python
tau = 1. / math.sqrt(Q.shape[-1])
scores = torch.matmul(Q, K.transpose(-2, -1))
max_per_query = scores.max(dim=-1, keepdims=True).values
A = torch.exp(tau * (scores - max_per_query))
A = A / torch.sum(A, axis=-1, keepdims=True)
O_m_with_max = torch.matmul(A, V)

print("O == O_m_with_max: ", torch.allclose(O, O_m_with_max, atol=1e-6))
```

    O == O_m_with_max:  True


## Forward Pass (Online Attention)

Instead of holding all of \\( Q, K, V \\) in memory, we want to compute attention block by block.

Let’s denote:

* \\( Q_{B_q} \in \mathbb{R}^{B_q \times d} \\): a block of queries
* \\( K_{B_k}, V_{B_k} \in \mathbb{R}^{B_k \times d} \\): a block of keys and values

where \\( B_q < N \\) and \\( B_k < M \\).

To see the idea more clearly, imagine the simplest case where \\( B_q = B_k = 1 \\):

* We process one query against one key–value pair at a time.
* As we stream through the keys/values, we maintain three running quantities:

  * \\( m_i^t \\): running maximum of scores (for stability)
  * \\( n_i^t \\): running numerator (vector)
  * \\( d_i^t \\): running denominator (scalar)

At step \\( t \\), when query \\( Q_i \\) sees the key–value pair \\( (K_t, V_t) \\), we update as follows:

\\[
m_i^t = \max \big(m_i^{t-1}, \, Q_i^\top K_t\big) \in \mathbb{R}
\\]

\\[
n_i^t = n_i^{t-1} \cdot \exp(m_i^{t-1} - m_i^t) \;+\; \exp(\tau Q_i^\top K_t - m_i^t) \, V_t \quad \in \mathbb{R}^d
\\]

\\[
d_i^t = d_i^{t-1} \cdot \exp(m_i^{t-1} - m_i^t) \;+\; \exp(\tau Q_i^\top K_t - m_i^t) \quad \in \mathbb{R}
\\]

The correction factor \\( \exp(m_i^{t-1} - m_i^t) \\) ensures consistency when the running maximum changes.

After processing all \\( M \\) keys, the final attention output for query \\( i \\) is simply:

\\[
O_{i,:} = \frac{n_i^M}{d_i^M}
\\]


> With this formulation, we only need to keep a block of queries, keys, and values in memory at a time, plus the running triplet \\( (m_i, n_i, d_i) \\). This makes it possible to compute attention streaming-style while staying numerically stable.



```python
block_size = 2
tau = 1. / math.sqrt(Q.shape[-1])

max_per_query = torch.full((B, L), float('-inf'), dtype=torch.float32) # one max per query
num = torch.zeros(B, L, D)
den = torch.zeros(B, L)

for start_idx in range(0, L, block_size):
    outer_range = range(start_idx, min(start_idx + block_size, L))
    K_b, V_b = K[:, outer_range], V[:, outer_range] # [B, BLOCK, D]

    for start_jdx in range(0, L, block_size):
        inner_range = range(start_jdx, min(start_jdx + block_size, L))
        Q_b = Q[:, inner_range]

        scores_b = tau * torch.matmul(Q_b, K_b.transpose(-2, -1))

        ## Bookkeeping
        m_old = max_per_query[:, inner_range]

        # compute new maximums
        m_new = max_per_query[:, inner_range] = torch.max(m_old, scores_b.max(axis=-1).values)
        
        # rescaling factors
        exp_delta_m = torch.exp(m_old - m_new).unsqueeze(-1)
        new_score_exp = torch.exp(scores_b  - m_new.unsqueeze(-1)) # Broadcast max to the last dimension

        # numerator
        num[:, inner_range] = num[:, inner_range] * exp_delta_m + torch.matmul(new_score_exp, V_b)

        # denominator 
        den[:, inner_range] = den[:, inner_range] * exp_delta_m.squeeze(-1) + new_score_exp.sum(dim=-1)

        
O_online = num/den.unsqueeze(-1)

print("O == O_online: ", torch.allclose(O, O_online, atol=1e-6))
```

    O == O_online:  True


## Backward Pass (Batch Attention)

At the end of the forward computation, we have access to:

* the denominator \\( d_i = d_i^M \\),
* the stability term \\( m_i = \max_j Q_i^\top K_j \\).

During the backward pass, our goal is to compute the gradients

\\[
\partial Q = \frac{\partial L}{\partial Q}, \quad 
\partial K = \frac{\partial L}{\partial K}, \quad 
\partial V = \frac{\partial L}{\partial V},
\\]

given \\( \partial O = \frac{\partial L}{\partial O} \\), where \\( L \in \mathbb{R} \\) is the loss.

For clarity, let’s drop the \\( \partial L/\partial \\) notation and just write \\( \partial O, \partial Q, \partial K, \partial V \\).

The shapes are as follows:

\\[
\partial O \in \mathbb{R}^{N \times d}, \quad
\partial Q \in \mathbb{R}^{N \times d}, \quad
\partial K \in \mathbb{R}^{M \times d}, \quad
\partial V \in \mathbb{R}^{M \times d}
\\]


Recall the forward equations:

\\[
O = P V
\\]

Taking derivatives gives (Refer to Appendix A if matrix differentiation is unfamiliar to you):

\\[
\partial V = P^\top \partial O \in \mathbb{R}^{M \times d}, \quad 
\partial P = \partial O V^\top \in \mathbb{R}^{N \times M}
\\]

Each row of \\( P \\) comes from a softmax over the corresponding row of the score matrix \\( S = QK^\top \\). Since all entries in a row are coupled, we must handle them together.

For a vector softmax \\( \mathbf{y} = \text{Softmax}(\mathbf{x}) \\):

\\[
\partial \mathbf{x} = \big(\text{diag}(\mathbf{y}) - \mathbf{y}\mathbf{y}^\top\big)\, \partial \mathbf{y}
\\]

Equivalently, using elementwise notation:

\\[
\frac{\partial y_i}{\partial x_j} = y_i (\delta_{ij} - y_j)
\\]

where \\( \delta_{ij} \\) is the Kronecker delta.

For the \\( i \\)-th row of \\( P \\):

\\[
\partial S_{i,:} = \big(\text{diag}(P_{i,:}) - P_{i,:} P_{i,:}^\top\big) \, \partial P_{i,:}
\\]

This can also be written compactly as:

\\[
\partial S_{i,:} = P_{i,:} \odot \big(\partial P_{i,:} - (\partial P_{i,:}^\top P_{i,:}) \mathbf{1}\big)
\\]

where \\( P_{i,:} \in \mathbb{R}^M \\) is treated as a column vector.

Finally, since \\( S = QK^\top \\):

\\[
\partial Q = \partial S K \in \mathbb{R}^{N \times d}, \quad 
\partial K^\top = Q^\top \partial S \in \mathbb{R}^{d \times M}
\\]


**Note:** If you’re fluent with matrix calculus, these steps are straightforward. If not, I’ll include an appendix at the end of the post showing the derivations in more detail.


```python
# simulating gradient wrt the loss
dO = torch.randn(B, L, D)
O.backward(dO) # perform backprop

# read off the gradients 
dQ = Q.grad 
dK = K.grad
dV = V.grad 

# # Handcoded batch attention
scores = tau * torch.matmul(Q, K.transpose(-2, -1))
P = torch.softmax(scores, dim=-1)
O_manual = torch.matmul(P, V)

print("O == O_manual: ", torch.allclose(O, O_manual, atol=1e-6))

# backward pass in batch updates
dV_manual = torch.matmul(sm.transpose(-2, -1), dO)

dP = torch.matmul(dO, V.transpose(-2, -1))
dScores = P * (dP -  (dP * P).sum(dim=-1).unsqueeze(-1))

dQ_manual = tau * torch.matmul(dScores, K) # multiply the scaling factor 
dK_manual = tau * torch.matmul(dScores.transpose(-2, -1), Q) # multiply the scaling factor 

print("dV == dV_manual: ", torch.allclose(dV, dV_manual, atol=1e-6))
print("dQ == dQ_manual: ", torch.allclose(dQ, dQ_manual, atol=1e-6))
print("dK == dK_manual: ", torch.allclose(dK, dK_manual, atol=1e-6))
```

    O == O_manual:  True
    dV == dV_manual:  True
    dQ == dQ_manual:  True
    dK == dK_manual:  True


## Backward Pass (Online Attention)

Computing gradients in the naïve way would require storing the **entire softmax matrix**. For long sequences, this is completely impractical.

For example, with a sequence length of 128K, the attention matrix has size \\( 128K \times 128K \\). At 32-bit precision, that’s **\~65 GB just for one example**. Clearly infeasible.

Instead, we follow the approach used in *FlashAttention*.

As in the forward pass, we stream over blocks of queries, keys, and values. The scores and softmax probabilities are recomputed on the fly. The key difference from the forward pass is that:

* We already have the stored row-wise maxima (\\( m_i \\)), so no need to maintain running maxima.
* We also have the stored denominators (\\( d_i \\)), so we can reuse them directly.

In the gradient formulas, a problematic term appears:

\\[
\partial P_{i,:}^\top P_{i,:}
\\]

This is a scalar dot product that gets broadcast across all components of \\( P_{i,:} \\). If computed naively, it prevents simple parallelization row-by-row.

The FlashAttention paper resolves this by rewriting the scalar as:

\\[
D_i = \partial P_{i,:}^\top P_{i,:} 
= \sum_{j} P_{ij}\,\partial P_{ij} 
= \sum_{j} P_{ij} \, (\partial O_i V_j)
\\]

Notice the last step:

\\[
D_i = \partial O_i \Big(\sum_j P_{ij} V_j\Big) = \partial O_i^\top O_i
\\]

This turns the awkward scalar-product term into something much cleaner: the dot product between \\( \partial O_i \\) and the forward output \\( O_i \\).

This trick is critical because it allows the backward pass to be parallelized efficiently, in the same streaming/blockwise fashion as the forward pass.


```python
block_size = 2
tau = 1. / math.sqrt(Q.shape[-1])

# given:
# max_per_query: max over the query-key inner product
# den: denominator sum exp (query, key inner product) per query


dQ_online = torch.zeros(B, L ,D)
dK_online = torch.zeros(B, L ,D)
dV_online = torch.zeros(B, L ,D)

for start_idx in range(0, L, block_size):
    outer_range = range(start_idx, min(start_idx + block_size, L))
    K_b, V_b = K[:, outer_range], V[:, outer_range] # [B, BLOCK, D]

    for start_jdx in range(0, L, block_size):
        inner_range = range(start_jdx, min(start_jdx + block_size, L))
        Q_b = Q[:, inner_range]
        dO_b = dO[:, inner_range]
        O_b = O[:, inner_range]

        # recompute local probs P_b exactly using global m, d for the query rows
        scores_b = tau * torch.matmul(Q_b, K_b.transpose(-2, -1)) 
        m_b = max_per_query[:, inner_range, None]
        d_b = den[:, inner_range, None] 
        P_b = torch.exp(scores_b - m_b) / d_b # these are exact attn weights 
        
        # computing the derivatives wrt V and P
        dV_b = torch.matmul(P_b.transpose(-2, -1), dO_b)
        dP_b = torch.matmul(dO_b, V_b.transpose(-2, -1))

        # computing the derivatives wrt scores
        D_i = (dO_b * O_b).sum(dim=-1)
        dScores_b = P_b * (dP_b -  D_i.unsqueeze(-1))

        # computing the derivatives wrt Q and K
        dQ_b = tau * torch.matmul(dScores_b, K_b) # multiply the scaling factor 
        dK_b = tau * torch.matmul(dScores_b.transpose(-2, -1), Q_b) # multiply the scaling factor 

        # accumulating these gradients
        dQ_online[:, inner_range] += dQ_b
        dK_online[:, outer_range] += dK_b
        dV_online[:, outer_range] += dV_b
        
print("dV == dV_online: ", torch.allclose(dV, dV_online, atol=1e-6))
print("dQ == dQ_online: ", torch.allclose(dQ, dQ_online, atol=1e-6))
print("dK == dK_online: ", torch.allclose(dK, dK_online, atol=1e-6))
```

    dV == dV_online:  True
    dQ == dQ_online:  True
    dK == dK_online:  True


## Appendix A: Computing derivatives of P and V

Here we will build the intuition to symbolically compute the derivative of O with respect to P and V,

\\[
O = PV  \in \mathcal{R}^{N \times d}
\\]

\\[
\partial V = P^T \partial O \in \mathcal{R}^{M \times d}, \qquad \partial P = \partial O V^T \in \mathcal{R}^{N \times M} \\
\\]


Let’s start with some definitions. In calculus, the **gradient** is just the derivative, and **differentials** are small changes in variables, also called **variations**.

Our goal is to understand how to get the gradients of the loss with respect to \\( P \\) and \\( V \\), i.e. \\( \nabla_P L \\) and \\( \nabla_V L \\), when we already know the gradient with respect to \\( O \\), denoted \\( \nabla_O L \\). Here the relation is

\\[
O = P V, \quad O, P, V \in \mathbb{R}^{N \times D}.
\\]


**Step 1. Variations of \\( O \\)**

The first step is to ask: if \\( P \\) and \\( V \\) change a little bit, how does \\( O \\) change? Denote these small changes by \\( \delta P \\), \\( \delta V \\), and \\( \delta O \\).

For the function \\( f(P,V) = P V \\), the change in output is

\\[
\delta O = P \,\delta V + \delta P \,V.
\\]

This is just the usual product rule, written in matrix form: wiggle \\( P \\), you get \\( \delta P V \\); wiggle \\( V \\), you get \\( P \delta V \\).


**Step 2. Variation of the loss**

Now we want to see how the loss \\( L \\) changes when \\( O \\) changes. By definition, the variation in \\( L \\) is given by the inner product between the gradient and the perturbation:

\\[
\delta L = \mathrm{tr} \left( (\nabla_O L)^\top \delta O \right).
\\]

Substitute \\( \delta O = P \delta V + \delta P V \\):

\\[
\delta L = \mathrm{tr}\big((\nabla_O L)^\top P \,\delta V\big) + \mathrm{tr}\big((\nabla_O L)^\top \delta P V\big).
\\]


**Step 3: Rearranging with the trace identity**

Using the identity \\( \mathrm{tr}(ABC) = \mathrm{tr}(CBA) \\), we can move terms around so that \\( \delta V \\) and \\( \delta P \\) appear at the end:

\\[
\delta L = \mathrm{tr}\big((P^\top \nabla_O L)^\top \delta V\big) + \mathrm{tr}\big((\nabla_O L V^\top)^\top \delta P\big).
\\]

Now it’s clear which matrices multiply with \\( \delta V \\) and \\( \delta P \\).


**Step 4. Read off the gradients**

By definition of the trace/Frobenius inner product, the coefficients of \\( \delta V \\) and \\( \delta P \\) are the gradients we seek:

\\[
\nabla_V L = P^\top \nabla_O L,
\qquad
\nabla_P L = \nabla_O L V^\top.
\\]



## Appendix B: Full Attention with Dropout and Mask

Now that we’ve seen how to compute attention in an online fashion for both the forward and backward passes, let’s extend the formulation to include **dropout** and **masking**, which are standard in practice.

The overall structure remains the same, with just a few modifications:

* **Masking:** applied directly to the scores before softmax (e.g., causal mask or padding mask).
* **Dropout:** applied to the softmax probabilities \\( P \\) before they are multiplied by the values.

### Forward pass

* Compute scores block by block.
* Apply mask (setting masked positions to \\( -\infty \\) or a large negative number).
* Apply softmax with stability trick.
* Optionally apply dropout to the probabilities \\( P \\).
* Multiply by values \\( V \\) to get outputs.

### Backward pass

The backward pass follows the same blockwise structure as before, but with two additional considerations:

1. **Masking:** The same mask used in the forward pass must be reapplied to the scores in the backward pass to zero out contributions from masked positions.
2. **Dropout:** To remain consistent, the *exact same dropout pattern* used in the forward pass must be applied again during backpropagation. This requires careful handling of the random number generator (RNG) to ensure reproducibility.


⚠️ **Note:** Correct RNG management is subtle. In practice, frameworks like PyTorch handle dropout reproducibility automatically by saving RNG state between forward and backward. Implementing this manually in a custom kernel (e.g., for FlashAttention) requires special care, and we won’t go into the details here.

This way, the online attention mechanism is extended to the “real” transformer case: with masks for structure and dropout for regularization.


```python
B = 10
L = 20
D = 16
dropout_p = 0.
Q = torch.randn(B, L, D, requires_grad=True)
K = torch.randn(B, L, D, requires_grad=True)
V = torch.randn(B, L, D, requires_grad=True)
MASK = torch.ones(L, L, dtype=bool).tril(diagonal=0) # 0 offset from the diagonal

tau = 1. / math.sqrt(D)

# Using PyTorch Module
# API expects [B, heads, L, D]; here head dim = 1
O = F.scaled_dot_product_attention(Q.unsqueeze(1), K.unsqueeze(1), V.unsqueeze(1), attn_mask=MASK, dropout_p=dropout_p)
O = O.squeeze(1)

# Handcoded batch attention
scores = tau * torch.matmul(Q, K.transpose(-2, -1))
scores.masked_fill_(~MASK, float('-inf')) # apply mask
P = torch.softmax(scores, dim=-1)

# dropout on some attention weights 
keep_prob = 1 - dropout_p
dropout_mask = (torch.rand_like(P) < keep_prob).to(sm.dtype)
P = P * dropout_mask / keep_prob # We divide by keep_prob so that we don't have to multiply this factor at the test time

O_manual = torch.matmul(P, V)
print(f"O == O_manual (True if dropout_p = 0.0, current dropout: {dropout_p}): ", torch.allclose(O, O_manual, atol=1e-6))


## Computing backwards

# simulate gradients of loss wrt O
dO = torch.rand_like(O)
O.backward(dO)
dQ = Q.grad 
dK = K.grad 
dV = V.grad

dV_manual = torch.matmul(P.transpose(-2, -1), dO)
dP = torch.matmul(dO, V.transpose(-2, -1))
dP = dP * dropout_mask / keep_prob
dScores = P * (dP - (dP * P).sum(dim=-1).unsqueeze(-1))
dQ_manual = tau * torch.matmul(dScores, K) # multiply the scaling factor 
dK_manual = tau * torch.matmul(dScores.transpose(-2, -1), Q) # multiply the scaling factor 

print("dV == dV_manual: ", torch.allclose(dV, dV_manual, atol=1e-6))
print("dQ == dQ_manual: ", torch.allclose(dQ, dQ_manual, atol=1e-6))
print("dK == dK_manual: ", torch.allclose(dK, dK_manual, atol=1e-6))

```

    O == O_manual (True if dropout_p = 0.0, current dropout: 0.0):  True
    dV == dV_manual:  True
    dQ == dQ_manual:  True
    dK == dK_manual:  True



