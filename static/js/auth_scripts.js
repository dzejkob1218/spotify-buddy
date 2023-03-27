/* These scripts are only loaded if the user is authorized */
    $( document ).ready(function() {
       loadCurrentlyPlaying();
       /* Refresh currently playing every 5 seconds */
       setInterval(function() {
            loadCurrentlyPlaying()
        }, 5000);
    });

    function loadCurrentlyPlaying(){
            $.ajax({
                type: 'GET',
                url: '/_current',
                success: function(data) {
                  $( "#currentlyPlaying" ).html(data);
                  $( "#currentlyPlaying" ).fadeIn(500);
                }
            });
    }