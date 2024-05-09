---
layout: singlePage
title: "Resources"
permalink: /teaching/tutorials
---


## <i class="fa fa-chevron-right"></i> Tutorials

<div class="table-container">
  <table class="table table-hover">

    {% bibliography -f tutorials --template resourcesTemplate %}

  </table>

</div>

<div>

  <script type="text/javascript">
    function randomPastelColor() {
      const hue = Math.random() * 360;  // Random hue from 0 to 360
      const saturation = 0.5 + Math.random() * 0.2;  // Saturation between 50% and 70%
      const lightness = 0.7 + Math.random() * 0.3;  // Lightness between 70% and 100%
      return chroma.hsl(hue, saturation, lightness);
    }

    document.addEventListener('DOMContentLoaded', function() {
        const rows = document.querySelectorAll('tr');
        let allTags = [];
        let activeTags = new Set();  // Store active tags

        // Extract all tags and remove duplicates
        rows.forEach(row => {
            const tags = row.getAttribute('data-tags').split(', ').filter(Boolean);
            allTags = allTags.concat(tags);
        });
        const uniqueTags = [...new Set(allTags)];

        // Create buttons for each unique tag
        const sidebar = document.createElement('div');
        sidebar.id = 'sidebar';
        sidebar.class='col-md-2 col-sm-4'
        const container = document.querySelector('.table-container');
        container.appendChild(sidebar);

        const toggleBtn = document.createElement('button');
        toggleBtn.id = 'sidebarToggle';
        toggleBtn.textContent = 'Toggle Tags';


        sidebar.appendChild(toggleBtn);

        uniqueTags.forEach((tag, index) => {
            const button = document.createElement('button');
            button.style.backgroundColor = randomPastelColor().hex();;
            button.textContent = tag;
            button.onclick = () => {
                if (activeTags.has(tag)) {
                    activeTags.delete(tag);
                    button.classList.remove('active');
                } else {
                    activeTags.add(tag);
                    button.classList.add('active');
                }
                filterRows(activeTags);
            };
            sidebar.appendChild(button);
        });

        function filterRows(activeTags) {
            rows.forEach(row => {
                const tags = row.getAttribute('data-tags').split(', ').filter(Boolean);
                const matches = [...activeTags].some(tag => tags.includes(tag));
                row.style.display = matches || activeTags.size === 0 ? '' : 'none';
            });
        }
    });

    function toggleSidebar() {
      const content = document.getElementById('sidebarContent');
      if (content.style.display === 'block') {
          content.style.display = 'none';
      } else {
          content.style.display = 'block';
      }
    }


  </script>
</div>
