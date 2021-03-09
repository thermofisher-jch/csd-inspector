var reportEditorApp = {
    archiveId: null,
    archiveTypes: null,
    initialDisposition: null,
    elements: {
        editButton: $("#archive-edit"),
        cancelButton: $("#archive-cancel"),
        archiveIdentifier: $("#archive-identifier"),
        archiveSite: $("#archive-site"),
        archiveType: $("#archive-type"),
        archiveSummary: $("#archive-summary"),
        archiveFailureMode: $("#archive-failure-mode"),
        archiveIsKnownGood: $("#archive-is-known-good"),
        archiveTaser: $("#archive-taser"),
    },
    init: function (archiveId, archiveTypes, initialDisposition) {
        this.archiveId = archiveId;
        this.archiveTypes = archiveTypes;
        this.initialDisposition = initialDisposition;
        this.elements.archiveIsKnownGood.addClass("label");
        if (initialDisposition === 'T') {
            this.elements.archiveIsKnownGood.addClass("label-success");
            this.elements.archiveIsKnownGood.data('value', 'T');
            this.elements.archiveIsKnownGood.text("Known Good Run");
        } else if(initialDisposition === 'F') {
            this.elements.archiveIsKnownGood.addClass("label-warning");
            this.elements.archiveIsKnownGood.data('value', 'F');
            this.elements.archiveIsKnownGood.text("Known Issue Run");
        } else {
            this.elements.archiveIsKnownGood.addClass("label-info");
            this.elements.archiveIsKnownGood.data('value', 'K');
            this.elements.archiveIsKnownGood.text("Unknown Run");
        }
        this.elements.editButton.click(
            this.enable.bind(this));
        this.elements.cancelButton.click(function() {
		    window.location = '';
	    });
    },
    enable: function () {
        // Switch button to save button
        this.elements.editButton.html("<i class='icon-ok icon-white'></i> Save");
        this.elements.editButton.addClass("btn-primary");
        this.elements.cancelButton.removeClass("hide");
        this.elements.editButton.off('click');
        this.elements.editButton.click(this.save.bind(this));

        // Switch text to inputs
        [{
            element: this.elements.archiveIdentifier,
            fontSize: 25,
            type: "text",
            placeholder: "No Label"
        }, {
            element: this.elements.archiveSite,
            fontSize: 25,
            type: "text",
            placeholder: "No Site"
        }, {
            element: this.elements.archiveSummary,
            fontSize: 14,
            type: "text",
            placeholder: "No Summary"
        }, {
            element: this.elements.archiveFailureMode,
            fontSize: 14,
            type: "text",
            placeholder: "No Failure Mode"
        }, {
            element: this.elements.archiveTaser,
            fontSize: 14,
            type: "number",
            placeholder: "No TASER #"
        }].map(function (item) {
            var value = item.element.text = '::';
            item.element.html($("<input/>", {
                type: item.type,
                value: item.element.data("value"),
                placeholder: item.placeholder,
                style: "font-size:" + item.fontSize + "px;" +
                "height: auto;" +
                "vertical-align: top;" +
                "margin-bottom: 0px;" +
                "box-sizing: border-box;" +
                "width: 100%;"
            }))
        }.bind(this));

        //Switch toggle badge to checkbox widgets
        let knownGoodRadioBox = $('<ul class="disposition-radio"/>')
        const states = [
            ['K', 'Unknown'],
            ['T', 'Known Good'],
            ['F', 'Known Issue']
        ];
        states.forEach(function (type) {
            let attrs = {
                type: "radio",
                name: "is_known_good",
                class: "disposition-radio",
                value: type[0],
                id: "id_is_known_good_" + type[0],
            };
            const listElem = $('<li/>')
            const inputElem = $('<input/>', attrs)
            const labelElem = $('<label/>', { for: "id_is_known_good_" + type[0] })
            labelElem.text(type[1] + ': ');
            knownGoodRadioBox.append(
                listElem.wrapInner(inputElem).wrapInner(labelElem)
            );
            if (type[0] === this.initialDisposition) {
                inputElem.click();
            }
        }.bind(this));
        let outerLabel = $('<label/>', { id: 'archive-is-known-good' } );
        outerLabel.text('Run Outcome:');
        outerLabel.append(knownGoodRadioBox)
        this.elements.archiveIsKnownGood.replaceWith(outerLabel);
        this.elements.archiveIsKnownGood = outerLabel;

        // Switch machine type to select with option list.
        const archiveTypeSelect = $("<select/>", {
            type: "text",
            dir: "rtl",
            style: "font-size: 25px;" +
            "height: auto;" +
            "vertical-align: top;" +
            "margin-bottom: 0px;" +
            "height: 40px;" +
            "border-radius: 4px;" +
            "box-shadow: inset 0 1px 1px rgba(0, 0, 0, 0.075);" +
            "box-sizing: border-box;" +
            "width: 100%;"
        });
        this.archiveTypes.map(function (type) {
            archiveTypeSelect.append($("<option/>", {
                text: type.name,
                value: type.value,
                selected: this.elements.archiveType.data("value") === type.value
            }));
        }.bind(this));
        this.elements.archiveType.html(archiveTypeSelect);

    },
    save: function () {
        const knownRadioInputs = this.elements.archiveIsKnownGood.find("input");
        let isKnownGoodValue = 'K';
        for (ii of [0, 1, 2]) {
            if (knownRadioInputs[ii].checked) {
               isKnownGoodValue = knownRadioInputs[ii].value;
            }
        }
        $.ajax({
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },
            url: '/api/v1/Archive/' + this.archiveId + '/',
            type: 'PATCH',
            data: JSON.stringify({
                identifier: this.elements.archiveIdentifier.find("input").val(),
                site: this.elements.archiveSite.find("input").val(),
                archive_type: this.elements.archiveType.find("select").val(),
                summary: this.elements.archiveSummary.find("input").val(),
                failure_mode: this.elements.archiveFailureMode.find("input").val(),
                taser_ticket_number: this.elements.archiveTaser.find("input").val() || null,
                is_known_good: isKnownGoodValue,
            }),
            success: function (response, textStatus, jqXhr) {
            },
            error: function (jqXHR, textStatus, errorThrown) {
                alert("Error saving changes!");
            },
            complete: function () {
                window.location = "";
            }
        });
    }
};