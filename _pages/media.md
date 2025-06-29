---
layout: singlePage
title: "In The Media"
permalink: /media/
---

## Article Authored

<div markdown="0">
  {% assign authored_sorted = site.data.media.authored | sort: "date" | reverse %}
  {% for item in authored_sorted %}
    <a href="{{ item.link }}" class="article-card" target="_blank">
      <div class="article-content">
        <div class="article-main">
          <div class="article-title">
            <span class="title-text">{{ item.title }}</span>
          </div>
          <div class="outlet">
            <div class="outlet-info">
              <img src="{{ item.outlet_icon }}" alt="{{ item.outlet }}" class="outlet-icon">
              <span class="source">{{ item.outlet }}</span>
            </div>
            <span class="date">{{ item.date | date: "%b %Y" }}</span>
          </div>
        </div>
      </div>
    </a>
  {% endfor %}
</div>

## Media Coverage Featuring My Work

<div class="coverage-list" markdown="0">
  {% assign coverage_sorted = site.data.media.coverage | sort: "date" | reverse %}
  {% for item in coverage_sorted %}
    <a href="{{ item.link }}" class="coverage-item" target="_blank">
      <div class="coverage-content">
        <div class="coverage-main">
          <div class="coverage-title">
            <span class="title-text">{{ item.title }}</span>
          </div>
          <div class="outlet">
            <div class="outlet-info">
              <img src="{{ item.outlet_icon }}" alt="{{ item.outlet }}" class="outlet-icon">
              <span class="source">{{ item.outlet }}</span>
            </div>
            <span class="date">{{ item.date | date: "%b %Y" }}</span>
          </div>
        </div>
      </div>
    </a>
  {% endfor %}
</div>

<style>
.article-card {
  display: block;
  text-decoration: none;
  color: inherit;
  background: linear-gradient(145deg, #ffffff 0%, #f8f9fa 100%);
  padding: 2.5rem;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.08);
  margin: 2rem 0 3rem 0;
  border: 1px solid #e9ecef;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.article-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 16px rgba(0,0,0,0.12);
  text-decoration: none;
  color: inherit;
}

.article-content, .coverage-content {
  display: flex;
  justify-content: space-between;
  gap: 2rem;
  align-items: flex-start;
}

.article-main, .coverage-main {
  flex: 1;
}

.article-title, .coverage-title {
  margin-bottom: 1rem;
}

.title-text {
  font-size: 1.8rem;
  color: #2c3e50;
  line-height: 1.4;
  font-weight: 500;
  letter-spacing: -0.02em;
}

.article-card:hover .title-text, .coverage-item:hover .title-text {
  color: #2980b9;
}

.outlet {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1.5rem;
  margin-top: 0.8rem;
}

.outlet-info {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.5rem 1rem;
  background: linear-gradient(145deg, #ffffff 0%, #f8f9fa 100%);
  border: 1px solid #e1e8ed;
  border-radius: 50px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.04);
  transition: all 0.2s ease;
}

.outlet-info:hover {
  border-color: #2980b9;
  box-shadow: 0 2px 8px rgba(41,128,185,0.1);
  transform: translateY(-1px);
}

.outlet-icon {
  width: 32px;
  height: 32px;
  object-fit: contain;
}

.source {
  font-weight: 700;
  color: #2980b9;
  font-size: 1.4rem;
}

.date {
  color: #666;
  font-size: 1.4rem;
  font-weight: 500;
}

.coverage-list {
  display: flex;
  flex-direction: column;
  gap: 1.8rem;
}

.coverage-item {
  display: block;
  text-decoration: none;
  color: inherit;
  padding: 1.5rem;
  background: white;
  border: 1px solid #eee;
  border-radius: 8px;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.coverage-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0,0,0,0.1);
  text-decoration: none;
  color: inherit;
}

h2 {
  font-size: 2rem;
  color: #333;
  margin-bottom: 1.5rem;
  padding-bottom: 0.5rem;
  border-bottom: 2px solid #eee;
}
</style> 