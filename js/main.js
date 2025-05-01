// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
  // Get the button and dropdown elements
  const btn = document.getElementById('updates-btn');
  const dropdown = document.getElementById('updates-dropdown');

  if (!btn || !dropdown) {
    console.error('Updates elements not found:', {
      button: !!btn,
      dropdown: !!dropdown
    });
    return;
  }

  // Toggle dropdown
  btn.addEventListener('click', function(e) {
    e.preventDefault();
    e.stopPropagation();
    dropdown.classList.toggle('show');
  });

  // Close dropdown when clicking outside
  document.addEventListener('click', function(e) {
    if (!dropdown.contains(e.target) && !btn.contains(e.target)) {
      dropdown.classList.remove('show');
    }
  });

  // Close dropdown on escape key
  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape' && dropdown.classList.contains('show')) {
      dropdown.classList.remove('show');
    }
  });

  // Handle update item clicks
  const updateItems = document.querySelectorAll('.update-item');
  updateItems.forEach(item => {
    item.addEventListener('click', function(e) {
      // Don't trigger if clicking on any link
      if (e.target.closest('a')) {
        return;
      }
      
      // Only open the "Learn More" link when clicking on empty space
      const learnMoreLink = this.querySelector('.update-link');
      if (learnMoreLink) {
        window.open(learnMoreLink.href, '_blank');
      }
    });
  });
}); 