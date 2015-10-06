











$(document).ready(function($) {
   
    var mousewheelevt = (/Firefox/i.test(navigator.userAgent)) ? "DOMMouseScroll" : "mousewheel" //FF doesn't recognize mousewheel as of FF3.x

    $('#viewport').bind(mousewheelevt, function(e){

        var evt = window.event || e //equalize event object     
        evt = evt.originalEvent ? evt.originalEvent : evt; //convert to originalEvent if possible               
        var delta = evt.detail ? evt.detail*(-40) : evt.wheelDelta //check for detail first, because it is used by Opera and FF

        var el = $('.js-hide-on-scroll');

        if(delta > 0) {
            //scroll up
            el.removeClass('m-hide');
            el.addClass('m-show');
        }
        else{
            //scroll down
            el.addClass('m-hide');
            el.removeClass('m-show');
        }   
    });

    $('.js-menu-trigger').click(function() {
        $('.b-menu').addClass('m-active');
    });

// Sample Click Feature with overlay
// $('.triggerClass').click(function() {
//     $('.menuClass').toggleClass('m-active');
//     $('#overlay').toggleClass('m-active');
// });

// $('#overlay').click(function() {
//     $('.menuClass').removeClass('m-active');
//     $(this).removeClass('m-active');
// });

});