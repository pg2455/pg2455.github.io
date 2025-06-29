document.addEventListener('DOMContentLoaded', function() {
  var shareBtn = document.getElementById('share-btn');
  var popover = document.getElementById('share-popover');
  if (!shareBtn || !popover) return;

  shareBtn.addEventListener('click', function(e) {
    e.stopPropagation();
    if (popover.style.display === 'block') {
      popover.style.display = 'none';
    } else {
      popover.style.display = 'block';
      var rect = shareBtn.getBoundingClientRect();
      popover.style.top = (rect.bottom + window.scrollY + 8) + 'px';
      popover.style.left = (rect.left + window.scrollX) + 'px';
    }
  });

  document.addEventListener('click', function(e) {
    if (!popover.contains(e.target) && e.target !== shareBtn) {
      popover.style.display = 'none';
    }
  });
}); 