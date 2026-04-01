/**
 * Breadcrumb Dropdown Navigation
 *
 * Makes breadcrumb items clickable to show a dropdown of sibling pages
 * at that navigation level. Reads nav structure from the sidebar.
 */
(function () {
  'use strict';

  function init() {
    const breadcrumbs = document.querySelectorAll('.md-path__link');
    if (!breadcrumbs.length) return;

    breadcrumbs.forEach((crumb) => {
      const text = crumb.textContent.trim();
      if (!text || text === 'Home') return;

      // Find siblings at this nav level from the sidebar
      const siblings = findSiblings(text);
      if (siblings.length <= 1) return;

      // Make it interactive
      crumb.style.cursor = 'pointer';
      crumb.style.position = 'relative';

      crumb.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        toggleDropdown(crumb, siblings);
      });
    });

    // Close dropdown on outside click
    document.addEventListener('click', () => {
      document.querySelectorAll('.breadcrumb-dropdown').forEach((d) => d.remove());
    });
  }

  function findSiblings(text) {
    // Find the sidebar nav item matching this breadcrumb text
    const allNavItems = document.querySelectorAll('.md-nav__item');
    let parentList = null;

    for (const item of allNavItems) {
      const label =
        item.querySelector(':scope > .md-nav__link') ||
        item.querySelector(':scope > label .md-ellipsis');
      if (label && label.textContent.trim() === text) {
        parentList = item.parentElement;
        break;
      }
    }

    if (!parentList) return [];

    const siblings = [];
    parentList.querySelectorAll(':scope > .md-nav__item').forEach((item) => {
      const link = item.querySelector(':scope > .md-nav__link');
      const label = item.querySelector(':scope > label .md-ellipsis');
      const name = link
        ? link.textContent.trim()
        : label
          ? label.textContent.trim()
          : '';
      const href = link ? link.getAttribute('href') : null;

      if (name) {
        siblings.push({
          name,
          href,
          active: name === text,
        });
      }
    });

    return siblings;
  }

  function toggleDropdown(crumb, siblings) {
    // Remove existing
    document.querySelectorAll('.breadcrumb-dropdown').forEach((d) => d.remove());

    const dropdown = document.createElement('div');
    dropdown.className = 'breadcrumb-dropdown';

    siblings.forEach((s) => {
      const item = document.createElement('a');
      item.className = 'breadcrumb-dropdown-item' + (s.active ? ' active' : '');
      item.textContent = s.name;
      if (s.href) {
        item.href = s.href;
      } else {
        item.style.cursor = 'default';
      }
      dropdown.appendChild(item);
    });

    // Position below the breadcrumb
    const rect = crumb.getBoundingClientRect();
    dropdown.style.position = 'fixed';
    dropdown.style.top = rect.bottom + 4 + 'px';
    dropdown.style.left = rect.left + 'px';

    document.body.appendChild(dropdown);

    // Prevent this click from closing it
    dropdown.addEventListener('click', (e) => e.stopPropagation());
  }

  // Run after page loads (MkDocs instant navigation)
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  // Re-init on MkDocs instant navigation
  document.addEventListener('DOMContentSwitch', init);
  // Also handle location change for instant loading
  const observer = new MutationObserver(() => {
    // Small debounce
    clearTimeout(observer._timeout);
    observer._timeout = setTimeout(init, 200);
  });
  const content = document.querySelector('.md-content');
  if (content) {
    observer.observe(content, { childList: true, subtree: true });
  }
})();
