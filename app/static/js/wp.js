$(function() {
    // pull posts from wordpress.com api
    $.ajax({
        type: "GET",
        url: 'https://public-api.wordpress.com/rest/v1.1/sites/thegovlab.org/posts/?number=3',
        dataType: 'json',
    }).success( function(response){
        r = response;

        var slide = $( '.js-wp-slide' ).clone();
        $( '.js-template' ).remove();

        for (var post in r.posts) {
            var date = new Date(r.posts[post].date);
            $( slide ).find('.e-post-name').text( r.posts[post].title.replace(new RegExp('&#8217;', 'g'), "'") );
            $( slide ).find('.e-date').text( date.toDateString() );
            $( slide ).find('.e-post').html( r.posts[post].excerpt );
            // $( slide ).find('.e-read-more').attr( 'href', r.posts[post].URL );

            $( slide ).clone().appendTo( '#wp-slider' );
        }



        // $('#wp-slider').slick('unslick');
        $('#wp-slider').slick({
            arrows: true,
            draggable: false,
            swipeToSlide: true,
            autoplay: true,
            autoplaySpeed: 3000,
            responsive: [
            {
                breakpoint: 800,
                settings: {
                    draggable: true,
                }
            }
            ]
        });



    });


});