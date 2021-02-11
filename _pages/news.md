---
layout: singlePage
permalink: /news/
---
<br>
<br>
<h5 class="border-bottom border-gray pb-2 mb-0">Recent updates</h5>

<table class="table table-hover">
  {% if site.news  %}
  {% assign news = site.news | reverse %}
  {% for item in news limit: site.news_limit %}
    <tr>
      <td class="col-md-3"><strong>{{ item.date | date: "%b %-d, %Y" }}</strong></td>
      <td>{{ item.content | remove: '<p>' | remove: '</p>' | emojify }}</td>
    </tr>
  {% endfor %}
  {% else %}
  <p>No news so far...</p>
  {% endif %}
</table>
