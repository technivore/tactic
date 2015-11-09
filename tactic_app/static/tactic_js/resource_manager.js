/**
 * Created by bls910 on 11/1/15.
 */

var resourceManager = {
    show_add: true,
    show_multiple:false,
    show_new: false,
    show_load: true,
    show_view: true,
    show_duplicate: true,
    show_delete: true,
    show_loaded_list: false,
    show_save: false,
    res_type: "list",
    add_view: "/add_list",
    new_view: "",
    load_view: '',
    view_view: '/view_list/',
    duplicate_view: '/create_duplicate_list',
    delete_view: '/delete_list/',
    save_view: '',
    add_listeners: function () {
        $("#duplicate-" + this.res_type + "-button").click({"manager": this}, this.duplicate_func);
        $("#new-" + this.res_type + "-button").click({"manager": this}, this.new_func);
        $("#add-" + this.res_type + "-form").submit({"manager": this}, this.add_func);
        $("#view-" + this.res_type + "-button").click({"manager": this}, this.view_func);
        $("#load-" + this.res_type + "-button").click({"manager": this}, this.load_func);
        $("#delete-" + this.res_type + "-button").click({"manager": this}, this.delete_func);
        $("#save-" + this.res_type + "-button").click({"manager": this}, this.save_func);
    },

    add_func: function (event) {
        var manager = event.data.manager
        $.ajax({
            url: $SCRIPT_ROOT + manager.add_view,
            type: 'POST',
            data: new FormData(this),
            processData: false,
            contentType: false
        });
        event.preventDefault();
    },

    load_func: function (event) {
        var manager = event.data.manager
        var res_name = manager.check_for_selection(manager.res_type);
        if (res_name == "") return;
        window.open($SCRIPT_ROOT + manager.load_view + String(res_name))
    },

    view_func: function (event) {
        var manager = event.data.manager
        var res_name = manager.check_for_selection(manager.res_type);
        if (res_name == "") return;
        window.open($SCRIPT_ROOT + manager.view_view + String(res_name))
    },

    save_func: function (event) {
        var manager = event.data.manager
        var res_name = manager.check_for_selection(manager.res_type);
        if (res_name == "") return;
        window.open($SCRIPT_ROOT + manager.save_view + String(res_name))
    },


    duplicate_func: function (event) {
        var manager = event.data.manager
        var res_name = manager.check_for_selection(manager.res_type);
        if (res_name == "") return;
        showModal("Duplicate " + manager.res_type, "New " + manager.res_type + " Name", function (new_name) {
            var result_dict = {
                "new_res_name": new_name,
                "res_to_copy": res_name,
            };

            $.ajax({
                url: $SCRIPT_ROOT + manager.duplicate_view,
                contentType: 'application/json',
                type: 'POST',
                async: true,
                data: JSON.stringify(result_dict),
                dataType: 'json',
            });
        })
    },

    new_func: function (event) {
        var manager = event.data.manager
        showModal("New " + manager.res_type, "New " + manager.res_type + " Name", function (new_name) {
            var result_dict = {
                "new_res_name": new_name,
            };

            $.ajax({
                url: $SCRIPT_ROOT + manager.new_view,
                contentType: 'application/json',
                type: 'POST',
                async: true,
                data: JSON.stringify(result_dict),
                dataType: 'json',
            });
        })
    },

    delete_func: function (event) {
        var manager = event.data.manager
        var res_name = manager.check_for_selection(manager.res_type);
        if (res_name == "") return;
        $.post($SCRIPT_ROOT + manager.delete_view + String(res_name))
    },

    check_for_selection: function (res_type) {
        var res_name = $('#' + res_type + '-selector > .btn.active').text().trim();
        if (res_name == "") {
            doFlash({"message": "Select a " + res_type + " first.", "alert_type": "alert-info"})
        }
        return res_name
    },

    create_module_html: function () {
        var res = Mustache.to_html(resource_module_template, this);
        $("#" + this.res_type + "-module").html(res);
    }
}

function updateObject(o1, o2) {
    for (prop in o2) {
        if (o2.hasOwnProperty(prop)){
            o1[prop] = o2[prop]
        }
    }
}
