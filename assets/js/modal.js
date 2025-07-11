document.addEventListener('DOMContentLoaded', () => {
    const body = document.body;
    const modal = document.getElementById('article-modal');
    const modalContent = document.getElementById('modal-content');

    if (!modal || !modalContent) {
        console.error('Modal elements not found');
        return;
    }

    document.querySelectorAll('.article-card').forEach(card => {
        card.style.cursor = 'pointer';
        card.addEventListener('click', (e) => {
            // Stop propagation to prevent nested links from firing if any
            e.stopPropagation();
            e.preventDefault();

            const url = card.dataset.url;
            if (url) {
                openModalWithUrl(url);
            }
        });
    });
    
    function openModalWithUrl(url) {
        body.classList.add('modal-open');
        modal.classList.add('is-active');
        modalContent.innerHTML = '<p>Loading...</p>';

        fetch(url)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.text();
            })
            .then(html => {
                const parser = new DOMParser();
                const doc = parser.parseFromString(html, 'text/html');
                const article = doc.querySelector('.article-content');
                
                if (article) {
                    // To prevent images/scripts in fetched content from loading relative to the wrong path
                    // we can either fix src attributes, or just show the text content.
                    // For now, let's inject the whole thing and see.
                    modalContent.innerHTML = article.innerHTML;
                } else {
                    modalContent.innerHTML = '<p>Could not load article content. The selector ".article-content" might be incorrect.</p>';
                    console.error("Could not find '.article-content' in fetched document from URL:", url);
                }
            })
            .catch(err => {
                console.error('Failed to fetch article:', err);
                modalContent.innerHTML = `<p>Error loading article. ${err.message}</p>`;
            });
    }

    modal.addEventListener('mouseleave', () => {
        closeModal();
    });

    function closeModal() {
        modal.classList.remove('is-active');
        body.classList.remove('modal-open');
        modalContent.innerHTML = ''; // Clear content
    }
}); 