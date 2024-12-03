document.addEventListener('DOMContentLoaded', function() {
    // Function to handle rating update
    function handleRatingUpdate() {
        document.querySelectorAll('.rating label').forEach(function(star) {
            star.addEventListener('click', function() {
                const itemId = this.getAttribute('data-item-id');
                const rating = this.getAttribute('data-rating');

                fetch('/update_rating', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        update_id: itemId,
                        rating: rating
                    })
                }).then(response => response.json()).then(data => {
                    if (data.success) {
                        showConfirmationMessage('Rating updated');
                    }
                });
            });
        });
    }

    // Function to handle comment update
    function handleCommentUpdate() {
        document.querySelectorAll('.update-comment-button').forEach(function(button) {
            button.addEventListener('click', function() {
                const itemId = this.getAttribute('data-item-id');
                const comment = this.previousElementSibling.value;

                fetch('/update_comment', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        update_id: itemId,
                        comment: comment
                    })
                }).then(response => response.json()).then(data => {
                    if (data.success) {
                        showConfirmationMessage('Comment added');
                    }
                });
            });
        });
    }

    // Function to handle item deletion
    function handleItemDeletion() {
        document.querySelectorAll('.delete-button').forEach(function(button) {
            button.addEventListener('click', function() {
                const itemId = this.getAttribute('data-item-id');

                fetch('/delete_item', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        item_id: itemId
                    })
                }).then(response => response.json()).then(data => {
                    if (data.success) {
                        // showConfirmationMessage('Item deleted');
                        location.reload();
                    }
                });
            });
        });
    }

    // Function to show confirmation message
    function showConfirmationMessage(message) {
        const confirmationDiv = document.createElement('div');
        confirmationDiv.textContent = message;
        confirmationDiv.style.position = 'fixed';
        confirmationDiv.style.top = '20px';
        confirmationDiv.style.left = '50%';
        confirmationDiv.style.transform = 'translateX(-50%)';
        confirmationDiv.style.backgroundColor = '#fffdb5';
        confirmationDiv.style.color = 'black';
        confirmationDiv.style.padding = '10px 20px';
        confirmationDiv.style.borderRadius = '10px';
        confirmationDiv.style.boxShadow = '0px 4px 8px rgba(0, 0, 0, 0.1)';
        confirmationDiv.style.zIndex = '1000';
        confirmationDiv.style.opacity = '0';
        confirmationDiv.style.transition = 'opacity 0.8s';
        document.body.appendChild(confirmationDiv);

        setTimeout(() => {
            confirmationDiv.style.opacity = '1';
        }, 10);

        setTimeout(() => {
            confirmationDiv.style.opacity = '0';
            setTimeout(() => {
                confirmationDiv.remove();
            }, 400);
        }, 2000);
    }

    // Initialize handlers
    handleRatingUpdate();
    handleCommentUpdate();
    handleItemDeletion();

    // Search functionality with dropdown results
    const searchButtons = document.querySelectorAll('.search-button');
    const searchResults = {
        'book-search': document.getElementById('search-results-books'),
        'movie-search': document.getElementById('search-results-movies'),
        'music-search': document.getElementById('search-results-music')
    };

    document.addEventListener('click', function(event) {
        Object.values(searchResults).forEach(resultsDiv => {
            if (resultsDiv && !resultsDiv.contains(event.target)) {
                resultsDiv.style.display = 'none';
            }
        });
    });

    searchButtons.forEach(button => {
        button.addEventListener('click', function() {
            const searchType = this.getAttribute('data-search-type');
            const input = document.getElementById(`${searchType}-search`);
            const query = input.value.trim();

            if (query.length > 1) {
                const endpoint = searchType === 'book' ? '/search_books?query=' + query :
                    searchType === 'movie' ? '/search_movies?query=' + query :
                        '/search_music?query=' + query;

                fetch(endpoint)
                    .then(response => response.json())
                    .then(data => {
                        const resultsDiv = searchResults[`${searchType}-search`];
                        resultsDiv.innerHTML = '';
                        resultsDiv.style.display = 'block';
                        data.slice(0, 10).forEach(function(item) {
                            const div = document.createElement('div');
                            div.textContent = item.title + (item.author ? ' by ' + item.author : item.director ? ' (' + item.release_year + ') - Directed by ' + item.director : ' by ' + item.artist_name);
                            div.setAttribute('data-item-id', item.book_id || item.movie_id || item.music_id);
                            div.setAttribute('data-item-title', item.title);
                            div.addEventListener('click', function() {
                                input.value = item.title;
                                document.getElementById(`${searchType}-id-input`).value = item.book_id || item.movie_id || item.music_id;
                                resultsDiv.innerHTML = '';
                                resultsDiv.style.display = 'none';
                            });
                            resultsDiv.appendChild(div);
                        });
                    });
            }
        });
    });

    // Item addition with duplicate check handled by backend
    document.querySelectorAll('form.add-item-form').forEach(function(form) {
        form.addEventListener('submit', function(event) {
            event.preventDefault(); // Stop default form submission

            const itemType = form.querySelector('.search-button').getAttribute('data-search-type');
            const itemId = form.querySelector(`#${itemType}-id-input`).value;

            // Attempt to add item
            fetch('/add_item', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ item_id: itemId, item_type: itemType })
            }).then(response => response.json()).then(data => {
                showConfirmationMessage(data.message); // Show success or error message
                if (data.success) {
                    location.reload();  // Reload page to show updated data
                }
            });
        });
    });

    // Adjust font size for username depending on its length
    const usernameElement = document.querySelector('.welcome h2');
    const username = usernameElement.textContent.trim().replace('HI ', '').replace('!', '');

    usernameElement.style.fontSize = '38px';

    if (username.length > 8 && window.innerWidth <= 768) {
        usernameElement.style.fontSize = '20px';
    }
});




