>> To create a series of blogs, abide by the following convention -
1. Have a series identifier in each of their front matter as `series: name: zz id: x`
2. name of the file should be `YYYY-MM-DD-zz-x` where x denotes of the order of the post in the series


>> To use distillPost, your bibliography should be in `vendor/bibliography` following attributes are necessary:
distill: true
mathjax: true
bibliography: yy.bib


>> To add aditional styles to distillPost use _styles attribrute

>> To use maths inline : \\( math_expression \\)

>> To use full line expression:
\\[
full maths expression here
\\]


>> Mathjax is currently not working in <li></li> environments. 
