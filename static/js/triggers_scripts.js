$(document).ready(function() {

    $("#search-query").on("keyup focus", function(){
        let query = $(this).val();
        let type = $(".search-type-active").attr('data-type');
        searchSpotify(query, type);
    }).on('blur', hideSearch);

});