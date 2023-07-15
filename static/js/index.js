document.getElementById('search-form').addEventListener('submit', function(event) {
        event.preventDefault();

        var value = document.querySelector('input[name="tags"]').value;
        var formAction = '/search/' + value;

        this.action = formAction;
        this.submit();
    });
