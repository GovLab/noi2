(function(){
// set up the timeout variable
var t;
// setup the sizing function,
// with an argument that tells the chart to animate or not
function size(animate){
    // If we are resizing, we don't want the charts drawing on every resize event.
    // This clears the timeout so that we only run the sizing function
    // when we are done resizing the window
    clearTimeout(t);
    // This will reset the timeout right after clearing it.
    t = setTimeout(function(){
        $("canvas").each(function(i,el){
            // Set the canvas element's height and width to it's parent's height and width.
            // The parent element is the div.canvas-container
            $(el).attr({
                "width":$(el).parent().width(),
                "height":$(el).parent().outerHeight()
            });
        });
        // kickoff the redraw function, which builds all of the charts.
        redraw(animate);

        // loop through the widgets and find the tallest one, and set all of them to that height.
        var m = 0;
        // we have to remove any inline height setting first so that we get the automatic height.
        $(".widget").height("");
        $(".widget").each(function(i,el){ m = Math.max(m,$(el).height()); });
        $(".widget").height(m);

    }, 100); // the timeout should run after 100 milliseconds
}
$(window).on('resize', size);
function redraw(animation){
    var options = {};
    if (!animation){
        options.animation = false;
    } else {
        options.animation = true;
    }
    // ....
        // the rest of our chart drawing will happen here
    // ....
}
size(); // this kicks off the first drawing; note that the first call to size will animate the charts in.



new Chart(ctx).Radar(data, options);

});
