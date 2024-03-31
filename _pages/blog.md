---
layout: singlePage
title: "Blog Posts"
permalink: /blog/
---

# Blog Posts
<br>
{% assign postsByYear = site.posts | group_by_exp:"post", "post.date | date: '%Y'" %}

{% for year in postsByYear %}
  <h2>{{ year.name }}</h2>
  <table class="table table-hover">

    {% assign postsBySeries = year.items | group_by_exp:"item", "item.series.name" %}

      {% for series in postsBySeries %}
        {% if series.name %}
          {% assign series_items = series.items | reverse %}
          {% for post in series_items %}
          {% unless post.draft %}
            {% if forloop.first %}
            <tr>
              <td class="col-md-3 align-middle"><a href="{{ post.url }}">{{ post.icon }}</a></td>
              <td style="vertical-align:middle;"><a href="{{ post.url }}"><strong style="margin: 0 0 5px 0; font-size:1.25em;">{{ post.title }}</strong></a>
              <ul style="margin: 10px 0 0 0">
            {% else %}
              <li style="margin: 0 0 5px 0; font-size:1.1em;"><a href="{{ post.url }}"><em>{{ post.title }}</em></a></li>
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
            <td class="col-md-3"><a href="{{ post.url }}">{{ post.icon }}</a></td>
            <td style="vertical-align:middle;"><a href="{{ post.url }}"><strong style="margin: 0 0 5px 0; font-size:1.25em;">{{ post.title }}</strong></a></td>
          </tr>
          {% endunless %}
          {% endfor %}
        {% endif %}

      {% endfor %}
  </table>
{% endfor %}

