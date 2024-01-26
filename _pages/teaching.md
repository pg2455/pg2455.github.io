---
layout: singlePage
title: "Resources"
permalink: /teaching/
---

<br>

<ul class="vcenter list-inline idxIcons" style='font-size: 1em; margin-top:1em'>
  <li>
    <a href="#-tutorials" class="button1">Tutorials</a>
  </li>
  <li>
    <a href="#-courses" class="button1">Courses</a>
  </li>
  <li>
    <a href="#-hackathons" class="button1">Hackathons</a>
  </li>
</ul>

<br>

## <i class="fa fa-chevron-right"></i> Tutorials

<table class="table table-hover">

  {% bibliography -f tutorials --template resourcesTemplate %}

</table>

## <i class="fa fa-chevron-right"></i> Courses

<table class="table table-hover">

  {% bibliography -f courses --template resourcesTemplate %}

</table>

## <i class="fa fa-chevron-right"></i> Hackathons

<table class="table table-hover">

  {% bibliography -f hackathons --template resourcesTemplate %}

</table>
