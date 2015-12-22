/**
 * Created by bls910 on 6/12/15.
 */

var modal_template;
var tooltips_

$.get($SCRIPT_ROOT + "/get_modal_template", function(template){
    modal_template = $(template).filter('#modal-template').html();
});

function doFlash(data) {
    // Flash a bootstrap-styled warning in status-area
    // data should be a dict with message and type fields.
    // type can be alert-success, alert-warning, alert-info, alert-danger
    $("#status-area").fadeOut(function () {
        if (!data.hasOwnProperty("alert_type")){
            data.alert_type = "alert-info"
        }
        if (!data.hasOwnProperty("message")){
            data.message = "Unspecified message"
        }
        var alert_template = "<div class='alert {{alert_type}} alert-dismissible'>" +
            '<button type="button" class="close" data-dismiss="alert" aria-label="Close"><span aria-hidden="true">&times;</span></button> {{message}}</div>'

        var result = Mustache.to_html(alert_template, data);

        $("#status-area").html(result);
        $("#status-area").fadeIn();
    })
}

function tooltipper() {
    return tooltip_dict[this.id];
}

opts_top = {
    delay: { "show": 1000, "hide": 100 },
    title: tooltipper,
    placement: "top"
};

opts_bottom = {
    delay: { "show": 1000, "hide": 100 },
    title: tooltipper,
    placement: "bottom"
};

function initializeTooltips() {
    $('.tooltip-top[data-toggle="tooltip"]').tooltip(options=opts_top);
    $('.tooltip-bottom[data-toggle="tooltip"]').tooltip(options=opts_bottom);
}

function toggleTooltips() {
    $('[data-toggle="tooltip"]').tooltip('toggle')
    return (false)
}

function clearStatusArea() {
    $("#status-area").fadeOut()
}

function showModal(modal_title, field_title, submit_function, default_value) {
    data_dict = {"modal_title": modal_title, "field_title": field_title};

    var res = Mustache.to_html(modal_template, {
        "modal_title": modal_title,
        "field_title": field_title
    });
    $("#modal-area").html(res);
    $('#modal-dialog').on('shown.bs.modal', function () {
        $('#modal-text-input-field').focus();
    });
    $("#modal-dialog").modal();

    if (!(default_value == undefined)) {
        $("#modal-text-input-field").val(default_value)
    }

    $("#modal-submit-button").on("click", submit_handler);


    $('.submitter-field').keypress(function(e) {
        if (e.which == 13) {
            submit_handler();
            e.preventDefault();
        }
    });

    function submit_handler() {
        $("#modal-dialog").modal("hide");
        submit_function($("#modal-text-input-field").val())
    }
}