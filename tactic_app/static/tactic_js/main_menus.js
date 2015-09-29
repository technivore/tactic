/**
 * Created by bls910 on 8/1/15.
 */

var menus = {};
var menu_item_index = {};
var column_menu;
var project_menu;
var tile_menu;
var mousetrap = new Mousetrap();
var menu_template;
$.get($SCRIPT_ROOT + "/get_menu_template", function(template){
    menu_template = $(template).filter('#menu-template').html();
})

// This is the menu_object base prototype
var menu_object = {
    menu_name: "",
    options: [],
    shortcuts: {},
    render_menu: function () {
        var self = this;
        var options_list = create_options_list();
        var res = Mustache.to_html(menu_template, {
            "menu_name": this.menu_name ,
            "options": options_list
        });
        return res

        function create_options_list() {
            var result = [];
            var scuts = menus[self.menu_name].shortcuts
            for (var i = 0; i < self.options.length; ++i) {
                var opt = self.options[i]
                if (scuts.hasOwnProperty(opt)){
                    var key_text = scuts[opt].keys[0]
                }
                else {
                    var key_text = ""
                }
                result.push({"option_name": opt, "key_text": key_text})
            }
            return result
        }
    },

    add_options_to_index: function () {
        for (var i = 0; i < this.options.length; ++i) {
            menu_item_index[this.options[i]] = this.menu_name
        }
    },

    remove_options_from_index: function() {
        for (var i = 0; i < this.options.length; ++i) {
            delete menu_item_index[this.options[i]]
        }
    },

    disable_items: function (disable_list) {
        for (var i = 0; i < disable_list.length; ++i) {
            this.disable_menu_item(disable_list[i])
        }
    },
    enable_items: function (enable_list) {
        for (var i = 0; i < enable_list.length; ++i) {
            this.enable_menu_item(enable_list[i])
        }
    },
    perform_menu_item: function (menu_id) {
    },
    disable_menu_item: function (item_id) {
        $("#" + item_id).closest('li').addClass("disabled");
        var menu = menus[menu_item_index[item_id]];
        if (menu.shortcuts.hasOwnProperty(item_id)) {
            var scut = menu.shortcuts[item_id]
            mousetrap.unbind(scut.keys);
            if (scut.hasOwnProperty("fallthrough")) {
                mousetrap.bind(scut.keys, function (e) {
                    scut.fallthrough()
                    e.preventDefault()
                })
            }
        }
    },
    enable_menu_item: function (item_id) {
        $("#" + item_id).closest('li').removeClass("disabled");
        var menu = menus[menu_item_index[item_id]];
        if (menu.shortcuts.hasOwnProperty(item_id)) {
            var scut = menu.shortcuts[item_id];
            //mousetrap.unbind(scut.keys);
            mousetrap.bind(scut.keys, function (e) {
                scut.command();
                e.preventDefault()
            })
        }
    }
}

function bind_to_keys(shortcuts) {
    for (option in shortcuts) {
        if (!shortcuts.hasOwnProperty()) continue;
        mousetrap.bind(option.keys, function(e) {
            option.command()
            e.preventDefault()
        });
    }
    mousetrap.bind(['command+s', 'ctrl+s'], function(e) {
        save_project();
        e.preventDefault()
    })
}


mousetrap.bind("esc", function() {
    if (tableObject.selected_header != null) {
        deselect_header(tableObject.selected_header)
    }
    broadcast_event_to_server("DehighlightTable", {});
})

function build_and_render_menu_objects() {
    // Create the column_menu object
    column_menu = Object.create(menu_object);
    column_menu.menu_name = "Column";
    column_menu.options = ["shift-left", "shift-right", "hide", "unhide", "add-column"];
    column_menu.perform_menu_item = column_command;
    menus[column_menu.menu_name] = column_menu;
    column_menu.add_options_to_index();

    // Create the project_menu object
    project_menu = Object.create(menu_object);
    project_menu.menu_name = "Project";
    project_menu.options = ["save-as", "save", "export-data"];
    project_menu.perform_menu_item = project_command;
    menus[project_menu.menu_name] = project_menu;
    project_menu.add_options_to_index();
    project_menu.shortcuts = {
        "save": {"keys": ['ctrl+s', 'command+s'],
                "command": save_project,
                "fallthrough": function () {
                    $('#save-project-modal').modal()
                }
        }
    }
    bind_to_keys(project_menu.shortcuts);

    // Create the project_menu object
    tile_menu = Object.create(menu_object);
    tile_menu.menu_name = "Tile";
    tile_menu.perform_menu_item = tile_command;
    menus[tile_menu.menu_name] = tile_menu;
    tile_menu.options = tile_types;
    tile_menu.add_options_to_index();

    // Create the project_menu object
    user_tile_menu = Object.create(menu_object);
    user_tile_menu.menu_name = "User Tile";
    user_tile_menu.perform_menu_item = tile_command;
    menus[user_tile_menu.menu_name] = user_tile_menu;
    user_tile_menu.options = user_tile_types;
    user_tile_menu.add_options_to_index();

    socket.on('update-loaded-tile-list', function(data) {
        //This fires if the user loads a new tile
        user_tile_menu.remove_options_from_index()
        user_tile_menu.options = data['user_tile_name_list']
        user_tile_menu.add_options_to_index()

        // remove all menus and re-render
        $("#menu-area .dropdown").remove();
        render_menus()
    });

    render_menus()
    function render_menus() {
        for (var m in menus) {
            if (menus.hasOwnProperty(m)) {
                $("#menu-area").append(menus[m].render_menu())
            }
        };
        $(".menu-item").click(function(e) {
            var item_id = e.currentTarget.id;
            var menu_name = menu_item_index[item_id]
            menus[menu_name].perform_menu_item(item_id)
            e.preventDefault()
        });
        disable_require_column_select()
        project_menu.disable_items(["save"])

    }
}

function column_command(menu_id) {
    var the_id = tableObject.selected_header;
    if (the_id != null) {
        switch (menu_id) {
            case "shift-left":
            {
                deselect_header(the_id)
                var parent_struct = tableObject.current_spec.header_struct.find_parent_of_id(the_id);
                parent_struct.shift_child_left(the_id);
                tableObject.build_table();
                break;
            }
            case "shift-right":
            {
                deselect_header(the_id)
                var parent_struct = tableObject.current_spec.header_struct.find_parent_of_id(the_id);
                parent_struct.shift_child_right(the_id);
                tableObject.build_table();
                break;
            }
            case "hide":
            {
                deselect_header(the_id);
                col_class = ".header" + the_id;
                $(col_class).fadeOut();
                tableObject.current_spec.hidden_list.push(the_id);
                resize_from_sub_headers($("#" + the_id).data("super_headers"))
                break;
            }
        }
    }
    else if (menu_id == "unhide") {
        tableObject.current_spec.hidden_list = [];
        tableObject.build_table();
    }
    else if (menu_id == "add-column") {
        $('#add-column-modal').modal();
    }
};

function project_command(menu_id) {
    switch (menu_id) {
        case "save-as":
        {
            $('#save-project-modal').modal();
            break;
        }
        case "save":
        {
            save_project();
            break;
        }
        case "export-data":
        {
            $('#export-data-modal').modal();
        }
    }
}

function tile_command(menu_id) {
    $("#name-tile-modal #name-tile-modal-field").val(menu_id)
    $("#name-tile-modal #tile-type").html(menu_id)
    $("#name-tile-modal").modal()
}

function disable_require_column_select(){
    column_menu.disable_items(["shift-left", "shift-right", "hide"])
}

function enable_require_column_select(){
    column_menu.enable_items(["shift-left", "shift-right", "hide"])
}

function save_project() {
    var result_dict = {
        "main_id": main_id
        //"tablespec_dict": tablespec_dict
    };
    $.ajax({
        url: $SCRIPT_ROOT + "/update_project",
        contentType : 'application/json',
        type : 'POST',
        async: false,
        data: JSON.stringify(result_dict),
        dataType: 'json',
        success: doFlash
    });
}

function export_data_table() {
    var export_name = $("#export-name-modal-field").val();
    var result_dict = {
        "export_name": export_name,
        "main_id": main_id,
    }
    $.ajax({
        url: $SCRIPT_ROOT + "/export_data",
        contentType : 'application/json',
        type : 'POST',
        async: true,
        data: JSON.stringify(result_dict),
        dataType: 'json',
        success: doFlash
    });
    $('#export-data-modal').modal('hide')
}

function save_project_as() {
    _project_name = $("#project-name-modal-field").val();
    var result_dict = {
        "project_name": _project_name,
        "main_id": main_id
        //"tablespec_dict": tablespec_dict
    };
    $.ajax({
        url: $SCRIPT_ROOT + "/save_new_project",
        contentType : 'application/json',
        type : 'POST',
        async: true,
        data: JSON.stringify(result_dict),
        dataType: 'json',
        success: save_as_success
    });
    $('#save-project-modal').modal('hide')
}

function create_column() {
    var column_name = $("#column-name-modal-field").val();
    // First: fix the header struct

    for (var doc in tablespec_dict) {
        if (tablespec_dict.hasOwnProperty(doc)) {
            var new_header_object = Object.create(header0bject)
            new_header_object.name = column_name;
            new_header_object.span = 1;
            new_header_object.depth = 0;
            new_header_object.id = tableObject.next_header_id;
            tableObject.next_header_id += 1;
            new_header_object.child_list = [];
            tablespec_dict[doc].header_struct.child_list.push(new_header_object)
        }
    }

    // Then rebuild the table
    tableObject.build_table()

    // Then change the current data_dict back on the server
    var data_dict = {"column_name": column_name,
                    "main_id": main_id};
    $.ajax({
        url: $SCRIPT_ROOT + "/distribute_events/CreateColumn",
        contentType : 'application/json',
        type : 'POST',
        async: true,
        data: JSON.stringify(data_dict),
        dataType: 'json',
    });
    $('#add-column-modal').modal('hide')
}

function save_as_success(data_object) {
    menus["Project"].enable_menu_item("save");
    tableObject.project_name = data_object["project_name"]
    //tableObject.set_table_title()
    $("#project-name").html(tableObject.project_name)
    data_object.alert_type = "alert-success"
    doFlash(data_object)
}


