var socket;


function start_post_load() {
    //spinner = new Spinner({scale: 1.0}).spin();
    //$("#loading-message").html(spinner.el);
    $("#outer-container").css({"margin-left": String(MARGIN_SIZE) + "px"});
    $("#outer-container").css({"margin-right": String(MARGIN_SIZE) + "px"});
    $("#outer-container").css({"margin-top": "0px", "margin-bottom": "0px"});
    $.getJSON($SCRIPT_ROOT + "/get_additional_params", function (data) {
        tile_types = data.tile_types;
        user_tile_types = data.user_tile_types;
        build_and_render_menu_objects();
    });
    if (_project_name != "") {
        $.getJSON($SCRIPT_ROOT + "/grab_project_data/" + String(main_id) + "/" + String(doc_names[0]), function(data) {
                $("#loading-message").css("display", "none");
                $("#reload-message").css("display", "none");
                $("#outer-container").css("display", "block");
                $("#table-area").css("display", "block");
                tablespec_dict = {};
                for (spec in data.tablespec_dict) {
                    if (!data.tablespec_dict.hasOwnProperty(spec)){
                        continue;
                    }
                    tablespec_dict[spec] = create_tablespec(data.tablespec_dict[spec])
                }
                tableObject.initialize_table(data);
                set_visible_doc(doc_names[0]) // It's important that this is done before creating the tiles
                var tile_ids = data.tile_ids;
                for (var i = 0; i < tile_ids.length; ++i) {
                    create_tile_from_save(tile_ids[i])
                }
                menus["Project"].enable_menu_item("save");

                // This is necessary in case the existence of any tiles requires changes to tile forms
                // It's a bit of a kluge since all of the forms will have been created once already
                broadcast_event_to_server("RebuildTileForms", {})
                //CameraTag.setup()
            })
    }
    else {
        $.getJSON($SCRIPT_ROOT + "/grab_data/" + String(main_id) + "/" + String(doc_names[0]), function (data) {
            $("#loading-message").css("display", "none");
            $("#reload-message").css("display", "none");
            $("#outer-container").css("display", "block");
            $("#table-area").css("display", "block");
            tablespec_dict = {};
            tableObject.initialize_table(data)
            set_visible_doc(doc_names[0])
            //CameraTag.setup()
        })
    }


    $("#tile-div").sortable({
        handle: '.panel-heading',
        tolerance: 'pointer',
        revert: 'invalid',
        forceHelperSize: true
    });
    socket = io.connect('http://' + document.domain + ':' + location.port + '/main');
    socket.emit('join', {"room": user_id});
    socket.emit('join', {"room": main_id});
    socket.on('tile-message', function (data) {
        // console.log("received tile message " + data.message);
        tile_dict[data.tile_id][data.message](data)
    });
    socket.on('table-message', function (data) {
        // console.log("received table message " + data.message);
        tableObject[data.message](data)
    });
    socket.on('close-user-windows', function(data){
        window.close()
    })
}

function set_visible_doc(doc_name) {
    $.getJSON($SCRIPT_ROOT + "/set_visible_doc/" + String(main_id) + "/" + String(doc_name))
}

function change_doc(el) {
    $("#table-area").css("display", "none");
    $("#reload-message").css("display", "block");
    doc_name = $(el).val()
    $.getJSON($SCRIPT_ROOT + "/grab_data/" + String(main_id) + "/" + String(doc_name), function (data) {
            $("#loading-message").css("display", "none");
            $("#reload-message").css("display", "none");
            $("#outer-container").css("display", "block");
            $("#table-area").css("display", "block");
            tableObject.initialize_table(data)
            set_visible_doc(doc_name)
        })
}

function broadcast_event_to_server(event_name, data_dict) {
    data_dict.main_id = main_id;
    data_dict.doc_name = tableObject.current_spec.doc_name;
    data_dict.active_row_index = tableObject.active_row;
    $.ajax({
        url: $SCRIPT_ROOT + "/distribute_events/" + event_name,
        contentType : 'application/json',
        type : 'POST',
        data: JSON.stringify(data_dict)
    });
}

spinner_html = '<span class="loader-small"></span>'

