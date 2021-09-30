$(document).ready(function() {
    loadPopovers();
    toggleSearchType($("#playlist-search-type"));
});

function toggleSearchType($selected) {
    $selected.toggleClass(["search-type", "search-type-active"]);
    $selected.prop('disabled', function (i, v) { // TODO: what the fuck is this
        return !v;
    });
}

function selectSearchType(clicked, focus=true) {
    toggleSearchType($(".search-type-active"));
    toggleSearchType($("#" + clicked));
    if (focus) {
        $("#search-query").trigger('focus');
    }
}

function requestDetails() {
    $.ajax({
        type: 'GET',
        url: '/_details',
        success: function (data) {
            $("#collection-tracks").toggle();
            $("#collection-filters").html(data['filters_html']);
            loadGradients(data['gradient_colors']);
            filtersFadeIn();
            $("#collection-tracks").html(data['tracklist_html']);
            $("#collection-tracks").fadeIn("slow");
        }
    });
}


function loadGradients(gradient_colors) {
    // Filter sliders
    let sliderGradient = 'linear-gradient(90deg, rgb(' + gradient_colors[0] + ') 0%, rgb(' + gradient_colors[1] + ') 100%)';
    $(".ui-slider-range").css('background', sliderGradient);
    // Switch sliders
    let switchGradient = 'linear-gradient(90deg, rgba(' + gradient_colors[0] + ', 0.7) 0%, rgba(' + gradient_colors[1] + ', 0.7) 100%)';

    $(".switchButton").css('background', switchGradient);
    // If there is a third color in the gradient, it's for the background of the page
    if (gradient_colors.length == 3) {
        let bgGradient = 'linear-gradient(0deg,  rgb(0,0,0) 0%, rgb(' + gradient_colors[2] + ') 100%)';
        $("#pageBody").css("background", bgGradient);
        setTimeout(bgFadeIn, 400);
    }

}


// TODO: why is this function like this?
function loadPopovers() {
    let popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    let popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl)
    });

}

/* Clears search results window */
function hideSearch() {
    $("#searchResults").html('');
}

function searchSpotify(query, type) {
    if (query || type == 'library') { // Don't require a query to request for user library
        $.ajax({
            type: 'GET',
            url: '/_search',
            data: {'q': query, 'type': type},
            success: function (data) {
                $("#searchResults").scrollTop(0);
                $("#searchResults").html(data);
            }
        });
    } else {
        hideSearch();
    }
}

function viewLibrary() {
    selectSearchType('library');
    $.ajax({
        type: 'GET',
        url: '/_library',
        success: function (data) {
            $("#searchResults").scrollTop(0);
            $("#searchResults").html(data);
        }
    });
}




/* Select item */
function selectItem(itemID, itemType, refresh = false) {
    hideSearch();
    if (itemType == 'track') {
        selectTrack(itemID);
    }

    if (itemType == 'playlist') {
        loadCollection(itemID, refresh);
    }
}

function loadCollection(collectionID, refresh = false) {
    $("#collection-details").fadeOut();
    $.ajax({
        type: 'GET',
        url: '/_collection',
        data: {'uri': collectionID, refresh: refresh},
        success: function (data) {
            $("#collection-details").html(data).fadeIn();
            requestDetails();
        }
    });


}

function selectTrack(trackID) {
    //$( "#trackDetails" ).fadeOut("fast");
    $.ajax({
        type: 'GET',
        url: '/_track',
        data: {'uri': trackID},
        success: function (data) {
            $("#selectedTrack").html(data);
            //adjustTrackDetails();
            loadQueuePopover();
            loadLyrics();
        }
    });
}

function adjustTrackDetails() {
    let $details = $("#track-details");
    let height = $details.height();
    $details.removeClass("flex-grow-1");
    $details.css("max-height", height);
}

function loadQueuePopover() {

    // Add a trigger to hide the queuing popover when shown
    $('#queueButton').on('shown.bs.popover', function () {
        setTimeout(function () {
            $('#queueButton').popover('hide');
        }, 1000);
    });

}

function loadLyrics() {
    $.ajax({
        type: 'GET',
        url: '/_lyrics',
        success: function (data) {
            $("#trackLyrics").html(data);
            $("#trackLyrics").scrollTop(0);
        }
    });
}

function playCollection(queue = false, number = 1, random = false) {
    $.ajax({
        type: 'POST',
        data: {
            queue: queue,
            number: number,
            random: random,
        },
        url: '/_play',
    });
}

function playTrack(queue = false) {
    if (queue) {
        $('#queueButton').popover('show');
    }
    $.ajax({
        type: 'POST',
        data: {
            queue: queue,
        },
        url: '/_play-track',
    });
}

function createPlaylist(name, number, random) {
    $.ajax({
        type: 'POST',
        data: {
            name: name,
            number: number,
            random: random,
        },
        url: '/_create'
    });

}


function getFilterChange(filter) {


    // TODO: simplify to loop with dictionary

    if (filter.hasClass('filter-slider')) {
        changes = getSliderChange(filter);
    }

    if (filter.hasClass('filter-switch')) {
        changes = getSwitchChange(filter);
    }
    // Return false if no changes were detected
    if (Object.keys(changes).length === 0) {
        return false;
    }
    // Return the dictionary of changes otherwise
    else {
        return changes;
    }
}


function getSwitchChange(filter) {
    let changes = {};
    if (filter.find(".switchTrue").hasClass('active')) {
        changes['switch'] = true;
    }
    if (filter.find(".switchFalse").hasClass('active')) {
        changes['switch'] = false;
    }
    return changes;
}


// Inspects a slider for changes in the values and returns them if different from defaults
// Also makes the labels of changed values bold (perhaps shouldn't be here)
function getSliderChange(filter) {
    let changes = {};
    let min = filter.slider("option", "min");
    let max = filter.slider("option", "max");
    let values = filter.slider("option", "values");
    let $labels = filter.find($(".slider-handle-label"));

    minChange = (values[0] !== min);
    maxChange = (values[1] !== max);

    $labels.eq(0).toggleClass('fw-bold', minChange);
    $labels.eq(1).toggleClass('fw-bold', maxChange);


    // The minimum value is changed
    if (minChange) {
        changes['min'] = values[0];
    }

    // The maximum value is changed
    if (maxChange) {
        changes['max'] = values[1];
    }

    return changes;

}


function formatDuration(ms) {
    var minutes = Math.floor(ms / 60000);
    var seconds = ((ms % 60000) / 1000).toFixed(0);
    return minutes + ":" + (seconds < 10 ? '0' : '') + seconds;
}

function createSlider(criterium, markers = null, average = 0, min = 0, max = 100, unit = '%') {
    // Create a new slider
    let newSlider = $("#slider-" + criterium);
    newSlider.slider({
        range: true,
        min: min,
        animate: "slow",
        max: max,
        values: [min, max],
        slide: function (event, ui) {
            // Change values displayed on the labels when sliding
            let $labels = $(this).find($(".slider-handle-label"));
            // TODO: Take formatting duration elsewhere
            $labels.eq(0).text(criterium == 'duration' ? formatDuration(ui.values[0]) : ui.values[0]);
            $labels.eq(1).text(criterium == 'duration' ? formatDuration(ui.values[1]) : ui.values[1]);
        }
    });

    // Paste custom slider handles
    let $handles = newSlider.find($(".ui-slider-handle"));
    $handles.eq(0).html($("#customHandleMin").clone());
    $handles.eq(1).html($("#customHandleMax").clone());

    // Initialize values on custom handles
    let $labels = newSlider.find($(".slider-handle-label"));
    //$labels.fadeToggle();
    $labels.eq(0).text(criterium == 'duration' ? formatDuration(min) : min);
    $labels.eq(1).text(criterium == 'duration' ? formatDuration(max) : max);

    //Clone range overlay
    newSlider.find(" .ui-slider-range").prepend($(".slider-range-overlay").first().clone());
    newSlider.find(" .ui-slider-range").css("min-width", "15px"); // Prevent from disappearing when handles are equal

    // Clone the slimmer background bar
    newSlider.prepend($(".filter-bar").first().clone());

    // Initialize the average marker
    if (average) {
        let $newMarker = $(".slider-marker").first().clone();
        newSlider.prepend($newMarker);
        relativePosition = 100 * (average / max);
        $newMarker.css("left", relativePosition + '%');
    }

    // Add event to make an ajax query when slider is changed
    newSlider.on("slidechange", function (event) {
        // If the slider is reset to its default state, don't send a new sorting criterium to the server
        updateFilters(getFilterChange($(this)) ? criterium : null);
    });
}

function switchFilter(attribute, value) {
    let yesSwitch = $("#" + attribute + "SwitchTrue");
    let noSwitch = $("#" + attribute + "SwitchFalse");

    if ((yesSwitch.hasClass('active') && value) || (noSwitch.hasClass('active') && !value)) {
        // The case where a selected button is pressed again, resetting the filter
        yesSwitch.toggleClass("active", false).toggleClass("inactive", false);
        noSwitch.toggleClass("active", false).toggleClass("inactive", false);
    } else {
        yesSwitch.toggleClass("active", value).toggleClass("inactive", !value);
        noSwitch.toggleClass("active", !value).toggleClass("inactive", value);
    }
    updateFilters(attribute);
}


function highlightFilter(filter, highlight, active = false) {
    if (filter.hasClass('filter-slider')) {
        highlightSlider(filter, highlight, active);
    }

    if (filter.hasClass('filter-switch')) {
        highlightSwitch(filter, highlight, active);
    }

}

function highlightSwitch(filter, highlight, active) {
    if (!active) {
        filter.find(".switchLabel").toggleClass('active', false).toggleClass('inactive', !highlight)
    }
}


// TODO: why does it use 'active' class instead of fading?
// Highlights or hides a slider filter with option for labels
function highlightSlider(slider, highlight, active) {
    if (highlight) {
        // Slider filters
        slider.find(".slider-range-overlay").removeClass("active").stop().fadeOut("slow");
        slider.find(".slider-handle-label").toggleClass("active", active);
    } else {
        slider.find(".slider-range-overlay").addClass("active").stop().fadeIn("slow");
        slider.find(".slider-handle-label").removeClass("active");
    }
}


function updateFilters(latestChange, explicitSort = false, sort_order = true) {

    // TODO: Explain the xReady flag situation nicely
    var fadeReady = false;
    var dataReady = false;
    var newList = null;

    // Fade the tracklist instantly to give the server some visual time to think
    $("#collection-tracks").fadeOut("fast", function () {
        fadeReady = true;
        if (dataReady) {
            $("#collection-tracks").html(newList);
            $("#collection-tracks").fadeIn("fast");
        }
    });

    let requestFilters = {};
    let changed = [];  // filters moved from min-max values by the user
    let inactive = []; // filters which haven't been touched by the user

    // Go through all filters and check for ones with values different than defaults
    // Save relevant information on changed filters into a dictionary to be sent to the server
    $(".filter").each(function () {
        let changes = getFilterChange($(this));
        if (changes) {
            // Save the data about the slider to be sent to server
            let criterium = $(this).attr('data-criterium');
            requestFilters[criterium] = changes;
            changed.push($(this));
        } else {
            inactive.push($(this));
        }
    });

    // Grey out inactive filters
    if (changed.length > 0) {
        inactive.forEach(function (filter) {
            highlightFilter(filter, false);
        });
        changed.forEach(function (filter) {
            highlightFilter(filter, true, active = true);
        });
        // If no filter is active, turn on colors on each
    } else {
        inactive.forEach(function (filter) {
            highlightFilter(filter, true);
        });
    }

    // Sends a query to the server to return sorted tracks, if explicitSort is true, the selected criterium will stick as the sorting key
    $.ajax({
        type: 'GET',
        url: '/_order',
        data: {
            sorting_details: JSON.stringify({
                filters: requestFilters,
                explicit_sort: explicitSort,
                sort_order: sort_order,
                sort_criterium: latestChange
            })
        },
        success: function (data) {
            dataReady = true;
            newList = data;
            if (fadeReady) {
                $("#collectionTracks").html(data);
                $("#collectionTracks").fadeIn("slow");
            }
        }
    });

}

function changePage(page) {

    var fadeReady = false;
    var dataReady = false;
    var newList = null;

    // Fade the tracklist instantly to give the server some visual time to think
    $("#collectionTracks").stop().fadeOut("fast", function () {
        fadeReady = true;
        if (dataReady) {
            $("#collectionTracks").html(newList);
            $("#collectionTracks").fadeIn("fast");
        }
    });

    $.ajax({
        type: 'GET',
        url: '/_page',
        data: {page: page},
        success: function (data) {
            dataReady = true;
            newList = data;
            if (fadeReady) {
                $("#collectionTracks").html(data);
                $("#collectionTracks").stop().fadeIn("slow");
            }
        }
    });
}


function sortTracks(criterium) {
    let sortOrder = true;

    let $allButtons = $('.collection-attribute');
    let $button = $('#' + criterium + 'Button');

    if ($button.hasClass('sort-normal')) {
        $button.removeClass('sort-normal');
        $button.addClass('sort-reverse');
        sortOrder = false;
    } else if ($button.hasClass('sort-reverse')) {
        $button.removeClass('sort-reverse');
        criterium = '';
    } else {
        $allButtons.removeClass("sort-normal");
        $allButtons.removeClass("sort-reverse");
        $button.addClass("sort-normal");
    }

    updateFilters(criterium, true, sortOrder);
}

function filtersFadeIn() {

    let $filters = $(".collection-attribute"),
        maxIndex = $filters.length,
        index = 0;


    interval = setInterval(function () {
        $filters.eq(index).fadeTo(400, 1, function () {


            // TODO: shouldn't this be done with higlight methods?
            // Show color on sliders (but only after checking they haven't already been disabled by user)
            $sliderOverlay = $(this).find(".slider-range-overlay");
            if (!$sliderOverlay.hasClass("active")) {
                $sliderOverlay.stop().fadeOut();
            }

            // Do the same for switches
            $switchOverlay = $(this).find(".switchLabel");
            $switchOverlay.removeClass('inactive');


            // Fade out the labels to create 'wave' effect
            $(this).find(".slider-handle-label").stop().fadeOut();

            // Add the labels fade effects on hover
            $(this).hover(
                function () {
                    $(this).find($(".slider-handle-label")).stop().fadeIn("fast");
                    $(this).find($(".attribute-clarification")).stop().fadeIn("fast");

                },
                function () {
                    $(this).find($(".slider-handle-label")).stop().fadeOut("fast");
                    $(this).find($(".attribute-clarification")).stop().fadeOut("fast");

                });
        });
        index++;
        if (index == maxIndex) {
            clearInterval(interval);
        }

    }, 80);
}

function bgFadeIn() {
    $("#bg-overlay").fadeOut(1000);
}