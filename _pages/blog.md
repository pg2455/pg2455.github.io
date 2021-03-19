---
layout: singlePage
title: "Blog Posts"
permalink: /blog/
---

# Blog Posts
<br>
<table class="table table-hover">
  {% assign postsByYear = site.posts | group_by_exp:"post", "post.date | date: '%Y'" %}

  {% for year in postsByYear %}
    <h2>{{ year.name }}</h2>
    {% assign postsBySeries = year.items | group_by_exp:"item", "item.series.name" %}

      {% for series in postsBySeries %}
        {% if series.name %}
          {% assign series_items = series.items | reverse %}
          {% for post in series_items %}
          {% unless post.draft %}
            {% if forloop.first %}
            <tr>
              <td class="col-md-3 align-middle"><a href="{{ post.url }}"><i class="{{ post.icon }}"></i></a></td>
              <td style="vertical-align:middle;"><a href="{{ post.url }}" style="color: black;"><strong>{{ post.title }}</strong></a>
              <ul>
            {% else %}
              <li><a href="{{ post.url }}"><strong>{{ post.title }}</strong></a></li>
            {% endif %}
            {% if forloop.last %}
            </ul>
            </td>
            </tr>
            {% endif %}
          {% endunless %}
          {% endfor %}

        {% else %}
          {% for post in series.items %}
          {% unless post.draft %}
          <tr>
            <td class="col-md-3"><a href="{{ post.url }}"><i class="{{ post.icon }}"></i></a></td>
            <td style="vertical-align:middle;"><a href="{{ post.url }}" style="text-decoration: none;color: black;"><strong>{{ post.title }}</strong></a></td>
          </tr>
          {% endunless %}
          {% endfor %}
        {% endif %}

      {% endfor %}

  {% endfor %}
</table>
