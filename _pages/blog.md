---
layout: singlePage
title: "Blog Posts"
permalink: /blog/
---
# Prateek's Blog Post
<br>
{% assign postsByYear = site.posts | group_by_exp:"post", "post.date | date: '%Y'" %}

{% for year in postsByYear %}
  <table class="table table-hover">

    {% assign postsBySeries = year.items | group_by_exp:"item", "item.series.name" %}

      {% for series in postsBySeries %}
        {% if series.name %}
          {% assign series_items = series.items | reverse %}
          {% for post in series_items %}
          {% unless post.draft %}
            {% if forloop.first %}
            <tr>
              <td class="col-md-12 align-middle" style="text-align:left;">
                <div style="margin-bottom: 0.25em; font-size: 0.95em; color: #888; text-align:left;">{{ post.date | date: "%b %d, %Y" }}</div>
                <a href="{{ post.url }}"><strong style="margin: 0 0 5px 0; font-size:1.25em; display: inline-block; text-align: left; width: 100%;">{{ post.title }}</strong></a>
                <ul style="margin: 10px 0 0 0; text-align:left;">
            {% else %}
              <li style="margin: 0 0 5px 0; font-size:1.1em; text-align:left;"><a href="{{ post.url }}">{{ post.title }}</a></li>
            {% endif %}
            {% if forloop.last %}
            </ul>
            <div style="margin: 10px 0 0 0; padding: 0.75em 1em; background: #f7f7f7; border-left: 4px solid #bdbdbd; border-radius: 6px; color: #666; font-size: 0.98em; max-width: 900px;">{{ series_items[0].excerpt | strip_html | truncate: 200 }}</div>
            </td>
            </tr>
            {% endif %}
          {% endunless %}
          {% endfor %}

        {% else %}
          {% for post in series.items %}
          {% unless post.draft %}
          <tr>
            <td class="col-md-12" style="text-align:left;">
              <div style="margin-bottom: 0.25em; font-size: 0.95em; color: #888; text-align:left;">{{ post.date | date: "%b %d, %Y" }}</div>
              <a href="{{ post.url }}"><strong style="margin: 0 0 5px 0; font-size:1.25em; display: inline-block; text-align: left; width: 100%;">{{ post.title }}</strong></a>
              <div style="margin: 10px 0 0 0; padding: 0.75em 1em; background: #f7f7f7; border-left: 4px solid #bdbdbd; border-radius: 6px; color: #666; font-size: 0.98em; max-width: 900px;">{{ post.excerpt | strip_html | truncate: 200 }}</div>
            </td>
          </tr>
          {% endunless %}
          {% endfor %}
        {% endif %}

      {% endfor %}
  </table>
{% endfor %}

