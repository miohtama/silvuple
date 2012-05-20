/**
 * Silvuple user interface Javascript
 */

 /*global window,document*/

(function($) {
     
    "use strict";


    /**
     * A dynamically populated table state machine switcher.
     *
     * @param  {Array} Listing of content items as Javascript array
     * @param  {Boolean} loading Should we display data or loading indicator
     * @param  {String} failureMessage Should we display failed to load message
     *
     */
    function renderContentListing(loading, failureMessage, items) {
       
        var data = {
            items : items,
            loadingStatus : loading,
            failureMessage : failureMessage
        };

        console.log(items);

        // What style attibute
        // we use to switch between states
        var visible = "display: block";
        var invisible = "display: none";

        // Use directives to switch between display states of different
        // list states by setting HTML style on the
        // different indicators elements
        var directives = {

            // Load failed
            failure : {
                style : function() { return this.failureMessage ? visible : invisible; }
            },

            // Load in progress
            loading : {
                style : function() { return this.loadingStatus ? visible : invisible; }
            },

            // Got the content
            listing : {
                style : function() { return this.items ? visible : invisible; }
            },

            // Format one entry in the listing
            "items" : {

                // Popuplate <a> from incoming data
                link : {
                    href : function() { return this["en"].link; },
                    text : function() { return this["en"].text; }
                }
            }
        };

        // Execute Transparency templating
        $(".translator-master-loader").render(data, directives);
    }


    function reloadContentListing() {

        // Initially set loader visible
        renderContentListing(true);

        function success(data) {
            // Got data from the server, proceed ->
            renderContentListing(false, null, data);
        }

        function fail(jqXHR, textStatus, errorThrown) {
            // Render HTTP status text as it is passed by server e.g. HTTP 500 Internal Server Error
            // as the failure message
            // (alternative extract error response from the HTTP reponse)

            // Don't pass undefined error message
            var message = jqXHR.statusText || textStatus;
            renderContentListing(false, message);
        }

        if(!window.silvupleOptions || !window.silvupleOptions.jsonContentLister) {
            throw new Error("Global Silvuple options object has not been initialized");
        }

        // Retrieve list data from a JSON callback
        // which has been passed us in a global JS helper object
        function fetch() {
            $.ajax({
              url: window.silvupleOptions.jsonContentLister,
              dataType: 'json',
              data: null,
              success: success,
              error : fail
            });
        }

        // Enter async processing
        fetch();

    }

    $(document).ready(function() {


        // Page has been loaded, put your custom JS logic here
        if($(".translator-master-loader").size() !== 0) {

            // Populate page for the first time
            reloadContentListing();
        }

    });

})(jQuery);

