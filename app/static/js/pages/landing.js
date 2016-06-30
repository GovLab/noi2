$(document).ready(function($) {
    var $overlay = $('#overlay');

    // Modal Logic
    $overlay.click(function() {
        $('.m-active').removeClass('m-active');
        $(this).removeClass('m-active');
    });

    // Slider Config (Sticky)
    $('#gallery-slider').slick({
        arrows: true,
        infinite: true,
        draggable: false,
        centerMode: true,
        slidesToShow: 1,
        variableWidth: true,
        focusOnSelect: true,
        swipeToSlide: true,
        responsive: [
            {
                breakpoint: 800,
                settings: {
                    draggable: true,
                    slidesToShow: 1,
                }
            }
        ]
    });
});