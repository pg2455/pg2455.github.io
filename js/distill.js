(function() {
  var tocBtn = document.getElementById('mobile-toc-toggle-btn');
  var tocContent = document.getElementById('mobile-toc-content');
  if (tocBtn && tocContent) {
    tocBtn.addEventListener('click', function() {
      var isOpen = tocContent.classList.toggle('open');
      tocBtn.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
      tocBtn.querySelector('span').innerHTML = isOpen ? '\u25B2' : '\u25BC';

      // Only remove heading when opening
      if (isOpen) {
        var myToc = tocContent.querySelector('my-toc');
        if (myToc) {
          var h2 = myToc.querySelector(':scope > h2');
          if (h2) {
            h2.parentNode.removeChild(h2);
          }
        }
      }
    });
  }

  // Custom TOC generation for all <my-toc> elements
  document.addEventListener('DOMContentLoaded', function() {
    var allTocs = document.querySelectorAll('my-toc');
    var article = document.querySelector('d-article');
    if (!article || allTocs.length === 0) return;
    var headings = article.querySelectorAll('h2, h3');
    allTocs.forEach(function(toc) {
      let ToC = `
        <style>
        my-toc { contain: layout style; display: block; }
        my-toc ul { padding-left: 0; }
        my-toc ul > ul { padding-left: 24px; }
        my-toc a { border-bottom: none; text-decoration: none; }
        </style>
        <nav role="navigation" class="table-of-contents"></nav>
        <h2>Table of contents</h2>
        <ul>`;
      headings.forEach(function(el) {
        const isInTitle = el.parentElement.tagName == 'D-TITLE';
        const isException = el.getAttribute('no-toc');
        if (isInTitle || isException) return;
        const title = el.textContent;
        const link = '#' + el.getAttribute('id');
        let newLine = '<li>' + '<a href="' + link + '">' + title + '</a>' + '</li>';
        if (el.tagName == 'H3') {
          newLine = '<ul>' + newLine + '</ul>';
        } else {
          newLine += '<br>';
        }
        ToC += newLine;
      });
      ToC += '</ul></nav>';
      toc.innerHTML = ToC;
    });
  });
})(); 