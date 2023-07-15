document.getElementById('form1').addEventListener('submit', function(event) {
        event.preventDefault();

        var value = document.querySelector('input[name="value1"]').value;
        var formAction = '/panel/c/User/' + value;

        this.action = formAction;
        this.submit();
    });
    document.getElementById('form2').addEventListener('submit', function(event) {
        event.preventDefault();

        var value = document.querySelector('input[name="value2"]').value;
        var formAction = '/panel/d/User/' + value;

        this.action = formAction;
        this.submit();
    });
    document.getElementById('form3').addEventListener('submit', function(event) {
        event.preventDefault();

        var value = document.querySelector('input[name="value3"]').value;
        var formAction = '/panel/c/Article/' + value;

        this.action = formAction;
        this.submit();
    });
    document.getElementById('form4').addEventListener('submit', function(event) {
        event.preventDefault();

        var value = document.querySelector('input[name="value4"]').value;
        var formAction = '/panel/d/Article/' + value;

        this.action = formAction;
        this.submit();
    });
