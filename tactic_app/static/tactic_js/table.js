/**
 * Created by bls910 on 7/11/15.
 */
// This controls how wide the widest field can be as
// a fraction of the containing panel
MAX_BIGFIELD_FRACTION = 1;
ADDED_HEADER_WIDTH = 35;
HEADER_SELECT_COLOR = "#9d9d9d";
HEADER_NORMAL_COLOR = "#c9e2b3";
TABLE_SELECT_COLOR = "#e0e0e0";
TABLE_NORMAL_COLOR = "#ffffff";
TABLE_BORDER_STYLE = "1px solid #9d9d9d;"
MAX_HEIGHT = 300;
MARGIN_SIZE = 5;
INITIAL_LEFT_FRACTION = .69

var td_template;
var th_template;
var th_template_resize;
var header_template;
var body_template;

$.get($SCRIPT_ROOT + "/get_table_templates", function(template){
    header_template = $(template).filter('#header-template').html();
    body_template = $(template).filter('#body-template').html();
})

function doSearch(t) {
    console.log("do search on " + t);
    var data_dict = {"text_to_find": t};
    broadcast_event_to_server("DehighlightTable", data_dict);
    if (t !== "") {
        broadcast_event_to_server("SearchTable", data_dict);
    }
    return false
}

function doFilter(t) {
    console.log("do filter on " + t);
    var data_dict = {"text_to_find": t};
    broadcast_event_to_server("UnfilterTable", data_dict);
    if (t !== "") {
        broadcast_event_to_server("FilterTable", data_dict);
    }
    return false
}

function doUnfilter(t) {
    broadcast_event_to_server("UnfilterTable", {});
    return false
}

function get_header(header_name) {
    return $("thead .column-" + header_name)
}
function get_column(header_name) {
    return $("tbody .column-" + header_name)
}

function deselect_header(header_name) {
    get_column(header_name).removeClass("selected-column");
    get_header(header_name).removeClass("selected-header");
    tableObject.selected_header = null
    disable_require_column_select()
}

function select_header(header_name) {
    get_column(header_name).addClass("selected-column")
    get_header(header_name).addClass("selected-header");
    tableObject.selected_header = header_name
    enable_require_column_select()
}

// This object stores information that defines how a table is displayed
// There will be one for each document in a table.
tableSpec = {
    "doc_name": null,
    "header_list": null,
    "hidden_list": [],
    "hidden_rows": [],
    "table_width": null,
    "column_widths": null,
    shift_column_left: function (column_name) {
        var i;
        for (i = 0; i < this.header_list.length; ++i) {
            if (this.header_list[i] == column_name) {
                if (i == 0) {
                    return;
                }
                else {
                    this.header_list.splice(i, 1)
                    this.header_list.splice(i - 1, 0, column_name)
                    var column_width = this.column_widths[i]
                    this.column_widths.splice(i, 1)
                    this.column_widths.splice(i - 1, 0, column_width)
                }
            }
        }
    },
    shift_column_right: function (column_name) {
        var i;
        for (i = 0; i < (this.header_list.length - 1); ++i) {
            if (this.header_list[i] == column_name) {
                this.header_list.splice(i, 1)
                this.header_list.splice(i + 1, 0, column_name)
                var column_width = this.column_widths[i]
                this.column_widths.splice(i, 1)
                this.column_widths.splice(i + 1, 0, column_width)
            }
        }
    }
}

function create_tablespec(dict) {
    var spec = Object.create(tableSpec);
    spec.doc_name = dict.doc_name;
    spec.header_list = dict.header_list;
    spec.hidden_list = dict.hidden_list;
    spec.hidden_rows = dict.hidden_rows;
    spec.table_width = dict.table_width;
    spec.column_widths = dict.column_widths;
    return spec
}

var tablespec_dict = {};

var tableObject = {
    table_id: "table-area",
    collection_name: null,
    data_rows: null,
    selected_header: null,
    highlighted_cells: [],

    initialize_table: function (data_object){
        this.highlighted_cells = []
        this.left_fraction = INITIAL_LEFT_FRACTION;
        this.left_fraction_save = this.left_fraction;
        this.collection_name = _collection_name;
        this.project_name = _project_name;
        //this.short_collection_name = _collection_name.replace(/^.*?\.data_collection\./, "");
        this.data_rows = data_object["data_rows"];
        this.current_doc_name = data_object["doc_name"]

        if (!tablespec_dict.hasOwnProperty(this.current_doc_name)) {
            this.current_spec = Object.create(tableSpec);
            this.current_spec.doc_name = this.current_doc_name;
            this.current_spec.hidden_list = ["__filename__"];
            this.current_spec.hidden_rows = [];
            this.current_spec.header_list = data_object["header_list"]
            tablespec_dict[this.current_doc_name] = this.current_spec;
        }
        else {
            this.current_spec = tablespec_dict[this.current_doc_name]
        }
        if (this.project_name == "") {
            menus["Project"].disable_menu_item('save')
        }
        this.build_table(); // This is separated out because it is called from elsewhere.
    },

    build_table: function() {
        var self = this;
        html_result = create_all_html(this.table_id, this.data_rows, this.current_spec.header_list);
        $("#" + this.table_id).html(html_result);
        for (i = 0; i < this.current_spec.hidden_list.length; ++i) {
            $(".column-" + this.current_spec.hidden_list[i]).css("display", "none");
        }
        this.hideRows(this.current_spec.hidden_rows);
        $("#project-name").html(this.project_name)
        setup_resize_listeners();
        this.resize_table_area();
        this.freeze_column_widths(this.table_id);
        broadcast_event_to_server("SaveTableSpec", {"tablespec": this.current_spec})
        $('#table-area td').blur(handle_cell_change)
        this.active_row = null;

        // Listen for the cursor to be placed in row
        $("#table-area").on('focus', 'td', function(e) {
              var row_index = $(this).closest("tr")[0].rowIndex - 1; //Substract one for the header row
              var old_row = $("#table-area tbody tr")[self.active_row]
              $(old_row).removeClass("selected-row")
              var new_row = $("#table-area tbody tr")[row_index]
              $(new_row).addClass("selected-row")
              self.active_row = row_index
        })

        // Listen for the user to click on a header
        $("#table-area th").on("click", function (event) {
            var el = event.target;
            var the_header = $(el).attr("id");
            if (the_header === self.selected_header) {
                deselect_header(the_header);
            }
            else {
                if (self.selected_header != null) {
                    deselect_header(self.selected_header)
                }
                select_header(the_header);
            }
        })

        $("#table-area td").mouseup(function (event) {
            var the_text = document.getSelection().toString();
            var the_dict;
            if (the_text.length > 0) {
                the_dict = {"selected_text": the_text};
                broadcast_event_to_server("TextSelect", the_dict)
            }
        })

        function create_all_html (table_id, data_rows, header_list) {
            //This method constructs all of the table html

            headers = []
            for (var i = 0; i < header_list.length; ++i) {
                headers.push({"header": header_list[i]})
            }
            var html_result = Mustache.to_html(header_template, {"headers": headers})

            var body_html = "";

            for (i = 0; i < data_rows.length; ++i) {

                cell_list = []
                for (var c = 0; c < header_list.length; ++c) {
                    cell_list.push({"rownumber": String(i), "header": header_list[c], "value": data_rows[i][header_list[c]]})
                }
                row_html = Mustache.to_html(body_template, {
                    "row_id": data_rows[i]["__id__"].toString(),
                    "cells": cell_list
                })
                body_html = body_html + row_html;
            }
            html_result += "<tbody>" + body_html + "</tbody>";
            return html_result;
        }

        function setup_resize_listeners() {
            $(".can-resize").resizable({
                handles: "e",
                resize: handle_resize,
                stop: save_column_widths
            })
            $("#table-area").resizable({
                handles: "e",
                stop: save_column_widths
            })
            $("#main-panel").resizable({
                handles: "e",
                resize: handle_resize
            })

            function handle_resize(event, ui) {
                if (this.tagName == "TH") {
                    new_width = ui.size.width
                    var header_element = ui.element;
                }
                if (this.tagName == "TD") {
                    var cellIndex = ui.element[0].cellIndex
                    var header_row_element = $("#table-area thead tr")[0]
                    var header_element = $(header_row_element.children[cellIndex])
                }
                if ((this.tagName == "TH") || (this.tagName == "TD")) {
                    var h_class = "column-" + header_element.attr("id");
                    $("." + h_class).innerWidth(ui.size.width);
                    $("." + h_class).css("maxWidth", ui.size.width);
                    self.current_spec.column_widths[ui.element[0].cellIndex] = ui.element[0].offsetWidth;
                }
                if (this.id == "main-panel") {
                    self.left_fraction = ui.size.width / (window.innerWidth - 2 * MARGIN_SIZE - 20);
                    self.resize_table_area();
                }
            }
        }

        function save_column_widths() {
            var col_cells = $("#table-area tbody tr:first td");
            var result = [];
            for (var i = 0; i < col_cells.length; ++i) {
                result.push(col_cells[i].offsetWidth)
            }
            self.current_spec.column_widths = result;
            self.current_spec.table_width = $("#table-area").width()

            broadcast_event_to_server("SaveTableSpec", {"tablespec": self.current_spec})
        }
        function handle_cell_change () {
            // This is called when the user directly edits a cell.
            // It is assumed that this points to the DOM element that was changed.
            var current_content = $(this).html();

            // turn any brs in the middle into newlines
            var rexp = new RegExp("\<br\>([\\w\\s])", "g")
            current_content = current_content.replace(rexp, "\\n")

            // get rid of any other tags and trim
            rexp = new RegExp("\<.*?\>", "g")
            current_content = current_content.replace(rexp, " ")
            current_content = current_content.trim()

            var rindex = this.parentElement.rowIndex - 1
            var cindex = this.cellIndex;
            var column_header = self.current_spec.header_list[cindex];;
            var old_content = self.data_rows[rindex][column_header]
            if (current_content != old_content) {
                shorter_sig = []
                //self.table_array[rindex][cindex] = current_content;
                this.data_rows[rindex][column_header] = current_content;
                data_dict = {
                    "row_index": rindex,
                    "column_header": column_header,
                    "old_content": old_content,
                    "new_content": current_content,
                    "doc_name": self.current_doc_name}
                broadcast_event_to_server("CellChange", data_dict)
            }
        }
    },

    freeze_column_widths: function (table_id) {
        // This modifies this.column_widths and this.table_width
        // This is only called by initialize_table.
        // But I split it out because it's so big.
        tidstr = "#" + table_id
        var ncols = this.current_spec.header_list.length
        var all_rows = $(tidstr).find("tr")
        column_widths = [];
        //this.big_fields = []

        var the_row;
        var the_width;
        var the_text;
        var the_child;

        var panel_width = $("#main-panel").width()
        var max_field_width = panel_width * MAX_BIGFIELD_FRACTION;

        if (this.current_spec.column_widths == null){
            this.current_spec.column_widths = []
        }
        // Within the code below we are trying to deal with the case where columns have been added to the end
        var cws = this.current_spec.column_widths.length;
        if (cws < ncols) {
            column_widths = this.current_spec.column_widths
            for (var c = cws; c < ncols; ++c) {
                column_widths.push(0);
                //this.big_fields.push(0)
            }
            // Get the max width of each column
            for (var r = 0; r < all_rows.length; ++r) {
                the_row = all_rows[r]

                for (c = cws; c < ncols; ++c) {
                    the_child = the_row.cells[c];
                    the_width = the_child.offsetWidth + ADDED_HEADER_WIDTH;
                    the_text = the_child.innerHTML;

                    if (the_width > max_field_width) {
                        the_width = max_field_width
                    }

                    if (the_width > column_widths[c]) {
                        column_widths[c] = the_width
                    }
                }
            }
            this.current_spec.column_widths = column_widths
            var total = 0;
            $.each(this.current_spec.column_widths, function() {
                total += this;
            })
            //this.table_width = total
            this.current_spec.table_width = total
            $("#" + this.table_id).width(String(total));
        }

        $("#" + this.table_id).width(String(this.current_spec.table_width))
        // Set all column widths
        var new_width;
        for (r = 0; r < all_rows.length; ++r) {
            the_row = all_rows[r];
            c = 0;
            while (c < ncols){
                the_child = the_row.cells[c];
                new_width = this.current_spec.column_widths[c];
                the_child.style.width = String(new_width) + "px";
                the_child.style.maxWidth = String(new_width) + "px";
                c += 1
            }
        }

        return
    },

    resize_table_area: function () {
        var usable_width = window.innerWidth - 2 * MARGIN_SIZE - 10;
        if (!(this.left_fraction == 0)) {
            $(".grid-left").width(usable_width * this.left_fraction);
        }
        $(".grid-right").width(usable_width * (1 - this.left_fraction))
        $("#status-area").width(usable_width)
        $("#table-area tbody").height(window.innerHeight - $("#console-panel").outerHeight() - 50 - $("#table-area tbody").offset().top)
        //$("#main-panel").outerHeight(window.innerHeight - $("#console-panel").outerHeight() - 50 - $("#main-panel").offset().top)
        $("#main-panel").width("") // We do this so that this will resize when the window is resized.
    },

    hideRows: function(hide_list) {
        var rows = $('#table-area tbody tr');
        for (i = 0; i < hide_list.length; ++i) {
            var rnum = hide_list[i];
            rows.eq(rnum).addClass("hidden-row")
        }
    },

    getCellElementByRowColIndex: function(rindex, cindex) {
        return $("#table-area tbody")[0].rows[rindex].cells[cindex]
    },

    dehighlightTxtInCell: function(data_object) {
        var rindex = data_object.row_index;
        var cheader = data_object.column_header;
        var cindex = this.current_spec.header_list.indexOf(cheader)
        try {
            var el = this.getCellElementByRowColIndex(rindex, cindex);
            el.innerHTML = el.innerHTML.replace(/<\/?span[^>]*>/g, "");
        }
        catch (err) {
            console.log(err.message + " row index " + rindex + "_col_index_ " + cindex)
        }
    },


    /* shrinkTable and expandTable are called from html inline */

    shrinkTable: function() {
        this.left_fraction_save = this.left_fraction;
        this.left_fraction = .05;
        //$(".grid-left")[0].classList.add("scaling-style");
        $(".grid-left").css("display", "none");
        $("#table-icon").css("display", "inline");
        this.resize_table_area();
        $(".tile-panel").addClass("tile-panel-float")
    },

    expandTable: function() {
        this.left_fraction = this.left_fraction_save;
        $("#table-icon").css("display", "none");
        $(".grid-left").css("display", "inline-block");
        this.resize_table_area();
        $(".tile-panel").removeClass("tile-panel-float")
    },

    /* The commands below will be called by the server with emit_table_message */

    setCellContent: function(data) {
        //It is assumed that this is called on the currently visible document only.
        //It will be called by the server, when the server wants to tell the client
        //there is a change in a cell in the visible document
        var cheader = data.column_header
        var new_content = data.new_content
        var row_index = data.id
        var cell_index = this.current_spec.header_list.indexOf(cheader)
        if (cell_index == -1) {
            console.log("invalid signature")
            return
        }
        var td_element = $("#table-area tbody")[0].rows[row_index].cells[cell_index];
        $(td_element).html(new_content)
        this.data_rows[row_index][cheader]= new_content
    },

    highlightTxtInCell: function(data_object) {
        var rindex = data_object.row_index;
        var cheader = data_object.column_header;
        var text_to_find = data_object.text_to_find;
        var cindex = this.current_spec.header_list.indexOf(cheader)
        try {
            var el = this.getCellElementByRowColIndex(rindex, cindex);
            var regex = new RegExp(text_to_find, "gi");
            el.innerHTML = el.innerHTML.replace(regex, function (matched) {
                    return "<span class=\"highlight \">" + matched + "</span>";
                });
            this.highlighted_cells.push({"row_index": rindex, "column_header": cheader})
        }
        catch(err) {
            console.log(err.message + " row index " + rindex + "_col_index_ " + cindex)
        }
    },

    colorTxtInCell: function(data_object) {
        var rindex = data_object.row_index;
        var cheader = data_object.column_header;
        var token_text = data_object.token_text;
        var color_dict = data_object.color_dict;
        var cindex = this.current_spec.header_list.indexOf(cheader)

        var result = "";

        try {
            var el = this.getCellElementByRowColIndex(rindex, cindex);
            for (var i = 0; i < token_text.length; ++i) {
                w = token_text[i]
                if (color_dict.hasOwnProperty(w)) {
                    result = result + "<span style='background-color: " + color_dict[w] + "' > " + w + "</span>";
                }
                else {
                    result = result + " " + w
                }
            }
            result = result.trim()
            el.innerHTML = result;
            this.highlighted_cells.push({"row_index": rindex, "column_header": cheader})
        }
        catch(err) {
            console.log(err.message + " row index " + rindex + "_col_index_ " + cindex)
        }
    },

    consoleLog: function(data_object) {
        if ($("#console").html() == "") {
            $("#console").append(data_object.message_string )
        }
        else {
            $("#console").append("<br>" + data_object.message_string )
        }
        $("#console")[0].scrollTop = $("#console")[0].scrollHeight
    },

    clearConsole: function(data_object) {
        $("#console").html("")
        $("#console")[0].scrollTop = $("#console")[0].scrollHeight
    },

    setHiddenRows: function(data_object) {
        var doc_name = data_object.document;
        if (!tablespec_dict.hasOwnProperty(doc_name)){
            return;
        }
        var hide_list = data_object.hide_list
        tablespec_dict[doc_name].hidden_rows = hide_list
        if (doc_name == this.current_spec.doc_name) {
            this.hideRows(data_object.hide_list)
        }
    },

    unfilterAllRows: function() {
        var rows = $('#table-area tbody tr');
        this.current_spec.hidden_rows.forEach(function(r){
            rows.eq(r).removeClass('hidden-row')
        });
        for (var spec in tablespec_dict) {
            if (!tablespec_dict.hasOwnProperty(spec)) continue;
            tablespec_dict[spec].hidden_rows = []
        }
    },

    dehiglightAllCells: function() {
        self = this;
        this.highlighted_cells.forEach(function(c){
            self.dehighlightTxtInCell(c)
        });
        this.highlighted_cells = []
    },

    startTableSpinner: function () {
        $("#table-spin-place").html(spinner_html);
    },

    stopTableSpinner: function () {
        $("#table-spin-place").html("");
    },

    rowup: function (clicked_element) {
          var $row = $(clicked_element).parents('tr');
          if ($row.index() === 1) return; // Don't go above the header
          $row.prev().before($row.get(0));
    },
    rowdown: function (clicked_element) {
          var $row = $(clicked_element).parents('tr');
          $row.next().after($row.get(0));
    },
    rowremove: function (clicked_element) {
        $(clicked_element).parents('tr').detach();
    }
}
