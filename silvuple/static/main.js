/**
 * Silvuple user interface Javascript
 */

 /*global window, document, console*/

(function($) {

    "use strict";

    // http://opensourcehacker.com/2011/03/15/everyone-loves-and-hates-console-log/
    // Ignore console on platforms where it is not available
    if (typeof(window.console) == "undefined") {
        window.console = {}; console.log = console.warn = console.error = function(a) {};
    }

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
                style : function() { return this.failureMessage ? visible : invisible; }
            },

            // Load in progress
            loading : {
                style : function() { return this.loadingStatus ? visible : invisible; }
            },

            // Got the content
            listing : {
                style : function() { return this.items ? visible : invisible; }
            },

            // Format one entry in the listing
            items : {

                // Populate <tr> from incoming data
                'listing-entry' : {

                    /**
                     * Populate an entry in a template dynamically using jQuery.
                     *
                     * This directive callback has *this* set to the current list element.
                     *
                     * @param  {Object} target Object of {index : list index, element : DOMNode, value : existing element text value}
                     */
                    html : function(target) {

                        // Convert raw DOM to jQuery Wrapper
                        // for modifying it in-place
                        var $elem = $(target.element);
                        var i;

                        // On the subsequent runs,
                        // make sure this element does not have any
                        // existing <td>s
                        $elem.empty();

                        // Example incoming data object
                        // [
                        // { language="de", availble=false }
                        // { language="en", available=true, url="http://localhost:9944/Plone/en", title="English Site version", canonical=true}
                        // ]

                        // Dynamically create <td> elements for each
                        // subitem in the data
                        for(i=0; i<this.length; i++) {

                            var item = this[i];

                            var td = $("<td>");

                            // Different elements we can generate
                            var actionLink = $("<a>");
                            var editLink = null;
                            var manageLink = null;
                            var note = null;

                            if(!item.available && item.language != "neutral") {

                                // Create quick translation links

                                if(item.canTranslate) {
                                    actionLink.text("Translate");
                                    actionLink.attr("href", item.url);
                                    actionLink.addClass("translate-link quick-link");
                                } else {
                                    actionLink.text("---");
                                    actionLink.attr("href", "#");
                                }
                            } else {

                                // Create go to and quick edit links

                                actionLink.text(item.title);
                                actionLink.attr("href", item.url);
                                actionLink.addClass("view-link");


                                editLink = $("<a>");
                                editLink.addClass("edit-link quick-link");
                                editLink.text("Edit");
                                editLink.attr("href", item.url + "/edit");
                            }

                            // Mark master language copy with
                            // .canonical-item CSS class
                            if(item.canonical) {

                                td.addClass("canonical-item");

                                note = $("<p>");
                                note.text(item.path);
                                note.addClass("note");

                                // TODO: translator manager page does not support
                                // AJAXy actions because it consists of 3 forms
                                manageLink = $("<a>");
                                manageLink.addClass("manage-link quick-link");
                                manageLink.text("Manage");
                                manageLink.attr("href", item.url + "/manage_translations_form");
                                manageLink.addClass("edit-link");
                            }

                            td.append(actionLink);

                            if(note) {
                                td.append(note);
                            }

                            if(editLink) {
                                td.append(editLink);
                            }

                            if(manageLink) {
                                td.append(manageLink);
                            }

                            $elem.append(td);
                        }

                        // Zebra-striping
                        if(target.index % 2 === 0) {
                            $elem.addClass("even");
                            $elem.removeClass("odd");
                        } else {
                            $elem.addClass("odd");
                            $elem.removeClass("even");
                        }

                    }
                }
            }

        };

        // Execute Transparency templating
        $(".translator-master-loader").render(data, directives);
    }


    /**
     * Actions to take when a AJAXy form is closed
     *
     * @return {String} prepOverlay action
     */
    function onShortcutFormClose() {

        console.log("onShortcutFormClose()");
        reloadContentListing();

        //  prepOverlay() API contract
        //  https://github.com/plone/plone.app.jquerytools/blob/master/plone/app/jquerytools/browser/overlayhelpers.js#L385
        return "close";
    }

    /**
     * Add jQuery Tools code for edit and translate pop-ups
     *
     * http://plone.org/products/plone.app.jquerytools
     */
    function installOverlayDelegates() {

        $('.translator-master-content .edit-link, .translator-master-content .translate-link').prepOverlay({
            subtype: "ajax",
            filter: "#content>*",
            formselector: "form",
            noform: onShortcutFormClose,
            closeselector: "[name=form.button.Cancel]",
            width : "90%"
        });

    }

    function reloadContentListing() {

        console.log("reloadContentListing()");

        // Initially set loader visible
        renderContentListing(true);

        function success(data) {
            // Got data from the server, proceed ->
            renderContentListing(false, null, data);

            installOverlayDelegates();
        }

        function fail(jqXHR, textStatus, errorThrown) {
            // Render HTTP status text as it is passed by server e.g. HTTP 500 Internal Server Error
            // as the failure message
            // (alternative extract error response from the HTTP reponse)

            // Don't pass undefined error message
            var message = jqXHR.statusText || textStatus;
            renderContentListing(false, message);
        }

        if(!window.silvupleOptions || !window.silvupleOptions.jsonContentLister) {
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
              error : fail,
              type : "POST" // Bust Varnish cache
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

            // installOverlayDelegates();
        }

    });

})(jQuery);

