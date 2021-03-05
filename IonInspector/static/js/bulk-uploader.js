/**
 * TODO: The following defines handling for a EVENT_UPLOAD_TASK_DELETED, but it does not have an
 *       event handler capable of receiving the required trigger from the Table Editor, and so has
 *       no way to triggers its own on-delete handling!!
 */
(function (window, document, undefined) {
        "use strict";
        // ie10+
        const ie10plus = window.navigator.msPointerEnabled;

        // let SUBMITTER_NAME = localStorage.getItem("submitter-name") || "";
        // function maybeUpdateName(newName) {
        //     if (newName !== SUBMITTER_NAME) {
        //         SUBMITTER_NAME = newName;
        //         localStorage.setItem("submitter-name", newName);
        //     }
        // }

        const ACCEPTED_SUFFIXES = [".zip", ".tar.gz", ".tar.xz", ".txz", ".tar", ".csv", ".log"]

        const DEBOUNCE_DELAY = 2;
        const MAX_CONCURRENT_UPLOADS = 2;
        const KNOWN_GOOD_OPTIONS =
            [{label: "\u2047", value: "K"}, {label: "\u2714", value: "T"}, {label: "\u2718", value: "F"}];
        const KNOWN_GOOD_OPTIONS_LOOKUP = {"K": "\u2047", "T": "\u2714", "F": "\u2718"};

        const VIEW_PROGRESS_REPORT = "ProgressReport";
        const VIEW_DATA_ENTRY = "DataEntry";

        const STATE_NEW = "---";
        const STATE_INCOMPLETE = "Incomplete Form";
        const STATE_READY = "Ready To Upload";
        const STATE_DUPLICATE = "Duplicate File";
        const STATE_IN_QUEUE = "Waiting In Queue";
        const STATE_IN_FLIGHT = "Uploading Now";
        const STATE_UPLOADED = "Successful Upload";
        const STATE_FAILED = "Failed Upload";
        const STATE_LOST = "Aborted Data Entry";
        const STATE_READY_LOST = "Aborted Upload";
        const STATE_FAILED_LOST = "Aborted Retry";

        const ON_RELOAD_STATE_MAP = {
            [[STATE_NEW]]: STATE_LOST,
            [[STATE_INCOMPLETE]]: STATE_LOST,
            [[STATE_READY]]: STATE_LOST,
            [[STATE_IN_QUEUE]]: STATE_READY_LOST,
            [[STATE_IN_FLIGHT]]: STATE_READY_LOST,
            [[STATE_UPLOADED]]: STATE_UPLOADED,
            [[STATE_FAILED]]: STATE_FAILED_LOST,
            [[STATE_LOST]]: STATE_LOST,
            [[STATE_READY_LOST]]: STATE_READY_LOST,
            [[STATE_FAILED_LOST]]: STATE_FAILED_LOST,
        };
        const STATE_TO_LABEL_COLOR_MAP = {
            [[STATE_INCOMPLETE]]: "warning",
            [[STATE_READY]]: "success",
            [[STATE_IN_QUEUE]]: "info",
            [[STATE_IN_FLIGHT]]: "primary",
            [[STATE_UPLOADED]]: "success",
            [[STATE_FAILED]]: "danger",
            [[STATE_LOST]]: "warning",
            [[STATE_READY_LOST]]: "info",
            [[STATE_FAILED_LOST]]: "danger",
            [[STATE_DUPLICATE]]: "danger",
        };

        const EDITABLE_FORM_STATES = new Set([STATE_NEW, STATE_INCOMPLETE, STATE_READY])
        const DATA_ENTRY_FORM_STATES = new Set([STATE_NEW, STATE_DUPLICATE, STATE_INCOMPLETE, STATE_READY])
        const LOST_FORM_STATES = new Set([STATE_LOST, STATE_FAILED_LOST, STATE_READY_LOST])
        const PROGRESS_VIEW_STATES = new Set([
            STATE_FAILED_LOST, STATE_LOST, STATE_READY_LOST, STATE_IN_FLIGHT, STATE_IN_QUEUE, STATE_UPLOADED, STATE_FAILED
        ])
        const DELETE_WITH_VERIFY_STATES = new Set([
            STATE_READY, STATE_INCOMPLETE,
        ])
        const DELETE_QUICKLY_STATES = new Set([
            STATE_DUPLICATE, STATE_UPLOADED, STATE_FAILED, STATE_FAILED_LOST,
            STATE_READY_LOST, STATE_IN_QUEUE, STATE_IN_FLIGHT, STATE_LOST
        ])

        const EVENT_DATA_ENTRY_DUPLICATED = "data-entry-duplicated";
        const EVENT_DATA_ENTRY_ADDED = "data-entry-added";
        const EVENT_DATA_ENTRY_UPDATED = "data-entry-updated";
        const EVENT_DATA_ENTRY_DROPPED = "data-entry-dropped";
        const EVENT_DATA_ENTRY_RECOVERED = "data-entry-file-recovered";
        const EVENT_DATA_ENTRY_TO_UPLOAD_TASK = "data-entry-to-upload-task";
        const EVENT_UPLOAD_TASK_RETRIED = "failed-retry-to-upload-queue";
        const EVENT_UPLOAD_TASK_IN_FLIGHT = "upload-task-in-flight";
        const EVENT_UPLOAD_TASK_SUCCEEDED = "upload-task-succeeded";
        const EVENT_UPLOAD_TASK_FAILED = "upload-task-failed";
        const EVENT_UPLOAD_TASK_RECOVERED = "upload-task-file-recovered";
        const EVENT_UPLOAD_TASK_DELETED = "upload-record-deleted";
        const EVENT_UPLOAD_QUEUE_IS_EMPTY = "upload-queue-is-empty";
        const EVENT_TOGGLE_OFF_REPORT_VIEW = "deactivate-report-view";
        const EVENT_TOGGLE_ON_ENTRY_VIEW = "activate-entry-view";
        const EVENT_TOGGLE_OFF_ENTRY_VIEW = "deactivate-entry-view";
        const EVENT_TOGGLE_ON_REPORT_VIEW = "activate-report-view";

        const PROP_LOCAL_KEY = "_local_key";
        const PROP_STATUS_MESSAGE = "_status_message";
        const PROP_NAME = "name";
        const PROP_SITE = "site_name";
        const PROP_LABEL = "archive_identifier";
        const PROP_TASER_TICKET_NUMBER = "taser_ticket_number";
        const PROP_IS_KNOWN_GOOD = "is_known_good";
        const PROP_DOC_FILE = "doc_file"

        const PATH_TO_METADATA = "_metadata."
        const PATH_STATUS_MESSAGE = PATH_TO_METADATA + PROP_STATUS_MESSAGE;
        const PATH_NAME = PATH_TO_METADATA + PROP_NAME;
        const PATH_SITE = PATH_TO_METADATA + PROP_SITE;
        const PATH_LABEL = PATH_TO_METADATA + PROP_LABEL;
        const PATH_TASER_TICKET_NUMBER = PATH_TO_METADATA + PROP_TASER_TICKET_NUMBER;
        const PATH_IS_KNOWN_GOOD = PATH_TO_METADATA + PROP_IS_KNOWN_GOOD;
        const PATH_DOC_FILE = PATH_TO_METADATA + PROP_DOC_FILE;

        const METADATA_DEFAULTS = {
            [[PROP_STATUS_MESSAGE]]: STATE_INCOMPLETE,
            [[PROP_NAME]]: localStorage.getItem("submitter-name") || "",
            [[PROP_SITE]]: "",
            [[PROP_LABEL]]: "",
            [[PROP_TASER_TICKET_NUMBER]]: "0",
            [[PROP_IS_KNOWN_GOOD]]: "K",
        };
        const USER_METADATA_PROPS = new Set(Object.keys(METADATA_DEFAULTS));
        const ALL_METADATA_PROPS = new Set(Object.keys(METADATA_DEFAULTS));
        ALL_METADATA_PROPS.add(PROP_DOC_FILE);
        ALL_METADATA_PROPS.add(PROP_LOCAL_KEY);
        ALL_METADATA_PROPS.add(PROP_STATUS_MESSAGE);

        function isArrayLike(obj) {
            return obj != null && typeof obj[Symbol.iterator] === "function";
        }

        function debounce(func, wait, immediate) {
            var timeout;

            return function executedFunction() {
                const context = this;
                const args = arguments;

                const later = function later() {
                    timeout = null;
                    if (!immediate) func.apply(context, args);
                };

                let callNow = immediate && !timeout;
                clearTimeout(timeout);
                timeout = setTimeout(later, wait);
                if (callNow) func.apply(context, args);
            };
        };

        /**
         * Small variation on jQuery's each() method that accepts a third cotext argument for overriding
         * jQuery's original behavior of using each iterated element to set the context value for 'this'.
         *
         * If the third context argument is not provided, this method behaves the same as jQuery's each
         * method.
         *
         * @param {Array|Object} obj object or an array to iterate
         * @param {Function} callback first argument is a value and second is a key.
         * @param {undefined|Object=} context Object to become context (`this`) for the iterator function.
         */
        function each(obj, callback, context = undefined) {
            if (!obj) {
                return;
            }
            let key;
            if (!context) {
                $.each(obj, callback);
                return;
            }
            if (isArrayLike(obj)) {
                for (key = 0; key < obj.length; key++) {
                    if (callback.call(context, key, obj[key]) === false) {
                        return;
                    }
                }
            } else {
                for (key in obj) {
                    if (callback.call(context, key, obj[key]) === false) {
                        return;
                    }
                }
            }
        }

        /**
         * Fixes the search order for extracting a display name from the File object provided by a browser
         * that has a handle on a given local file.
         *
         * @param file
         * @returns {string} The display name for file argument
         */
        function displayNameForFile(file) {
            return file.relativePath || file.webkitRelativePath || file.fileName || file.name;
        }

        function showReportIFrame(message, contextColor, location, htmlBody) {
            const myAlert = $(
                `<div id="show-content-modal" class="alert alert-${contextColor} alert-dismissible" role="alert">\n` +
                '  <button type="button" class="close btn btn-lg" data-dismiss="alert" aria-label="Close">\n' +
                '    <span class="glyphicon glyphicon-remove" aria-hidden="true"></span>\n' +
                '  </button>\n' + message +
                '</div>'
            );
            var iframe = document.createElement('iframe');
            myAlert.append(iframe);
            myAlert.appendTo($('body'));
            iframe.setAttribute("style", "height: calc(100% - 30px); width: 100%;");
            if (!!htmlBody) {
                iframe.contentWindow.document.open();
                iframe.contentWindow.document.write(htmlBody);
                iframe.contentWindow.document.close();
            } else if(!!location) {
                iframe.contentWindow.location = location;
            } else {
                // No use for the iframe this block.
            }
        }

        /**
         * UploadConfigStore manages state tracking submitted uploads, progress, completion, and failures.
         *
         * @paran inspectorVersion {string} Current Inspector release version string
         * @param emitter {EventEmitter}
         * @param csrfUrl {string} URL to get CSRF tokens from.
         * @param batchUploadUrl {string} URL to send uploaded files to.
         * @constructor
         */
        function UploadConfigStore(
            inspectorVersion, emitter, csrfUrl, batchUploadUrl
        ) {
            /**
             * Map by name to UploadableArchive objects
             * @type {Object.<String,UploadableArchive>}
             */
            this._files = {};
            this._activeView = undefined;
            this._inspectorVersion = inspectorVersion;
            this._emitter = emitter;
            this._csrfUrl = csrfUrl;
            this._batchUploadUrl = batchUploadUrl;
            this._initialized = false;

            // TODO: This should work like a chain of command.  Each handler from an older revision should
            //       produce the output that its successor expects as input instead of transforming all the
            //       way to the latest version.  Until then, each new revision will require editting each older
            //       handler, which will not scale
            /**
             * @callback loaderCallback - Method used to bootstrap store's _files property using
             *                            content serialized during a previous execution.  Registered
             *                            by an instance of {UpgradeRegistration} to establish a lower
             *                            bound on the range of saved payload objects it may accept.
             *                            These should be implemented as arrow methods created during
             *                            UploadConfigStore's constructor function call so they will
             *                            have implicitly bound this to that UploadConfigStore object.
             *                            Such arrow methods can optionally further delegate to methods
             *                            on UploadConfigStore's prototype that will bind this by object
             *                            dereferencing.
             * @param {Object.<string, string>} envelope - Metadata envelope attached to saved state
             * @param {string} envelope.savedAtVersion - Version at time of last save
             * @param {Object[]} payload - Content of payload array with data to restore.
             */

            /**
             * @typedef LoaderRegistration - Record in the list of loader registrations, which associates
             *                               a handler method with the first version of saved state it is
             *                               capable of loading into the current release's in memory state
             *                               model.
             * @type {{handler: loaderCallback, from: string}}
             * @property {string} from - The earliest release of Inspector this handler method can accept
             *                           payload objects from.  Must be earlier than all previous LoaderRegistrations,
             *                           and later than all subsequent LoaderRegistrations.
             * @property {loaderCallback} handler - The handler method to call if this record is selected as
             *                                      most compatible given previously saved state.
             */

            /**
             * @type {LoaderRegistration[]} List of loader registration records in sorted with their from
             *                              values in decreasing order, such that the first LoaderRegistration
             *                              to have a from value less than or equal to that of a given candidate
             *                              input has a handler for that candidate's persisted payload.
             * @private
             */
            this._supportedVersions = [
                /**
                 * @type {LoaderRegistration}
                 */
                {
                    from: "1.7.0-rc.3",
                    handler: (envelope, payload) => {
                        let rowState;
                        for (rowState of payload) {
                            const rowId = rowState[PROP_LOCAL_KEY];
                            rowState[PROP_STATUS_MESSAGE] = ON_RELOAD_STATE_MAP[rowState[PROP_STATUS_MESSAGE]];
                            this._files[rowId] = new UploadableArchive(
                                rowId, this._emitter, null, rowState, this._csrfUrl, this._batchUploadUrl
                            );
                        }
                    }
                },
                {
                    from: "1.6.4",
                    handler: (envelope, payload) => {
                        let rowState;
                        const MIGRATION_MAP = {
                            "---": STATE_NEW,
                            "Needs Input": STATE_INCOMPLETE,
                            "Incomplete Form": STATE_INCOMPLETE,
                            "Click Start": STATE_READY,
                            "Duplicate": STATE_DUPLICATE,
                            "Queued": STATE_IN_QUEUE,
                            "Sending Now": STATE_IN_FLIGHT,
                            "Uploaded": STATE_UPLOADED,
                            "Failed": STATE_FAILED,
                            "Needs File": STATE_LOST
                        }
                        for (rowState of payload) {
                            console.log("In:: ", rowState)
                            const rowId = rowState[PROP_LOCAL_KEY];
                            const before = rowState[PROP_STATUS_MESSAGE];
                            rowState[PROP_STATUS_MESSAGE] = ON_RELOAD_STATE_MAP[
                                MIGRATION_MAP[
                                    rowState[PROP_STATUS_MESSAGE]]];
                            const after = rowState[PROP_STATUS_MESSAGE]
                            this._files[rowId] = new UploadableArchive(
                                rowId, this._emitter, null, rowState, this._csrfUrl, this._batchUploadUrl
                            );
                            console.log(`${before} => ${after}`, this._files[rowId])
                            console.log("Out:: ", rowState)
                        }
                    }
                },
                /**
                 * @type {LoaderRegistration}
                 */
                {
                    from: "0.0.1",
                    handler: (envelope, payload) => {
                        // A default handler that just discards previous save state.
                        this._files = [];
                    }
                }
            ];

            this.initialDataLoader = (data, callback) => {
                callback({
                    data: Object.values(this._files).filter((x) => {
                        return x.isDataEntry();
                    })
                })
            };

            this.progressDataLoader = (data, callback) => {
                callback({
                    data: Object.values(this._files).filter((x) => {
                        return x.isReportable();
                    })
                })
            }

            this._commitLocalStorage = debounce(() => {
                localStorage.setItem(
                    'client_upload_state',
                    JSON.stringify({
                        envelope: {
                            savedAtVersion: this._inspectorVersion
                        },
                        payload: Object.values(this._files)
                            .filter((x) => x._metadata._status_message !== STATE_DUPLICATE)
                            .map((x) => x._metadata)
                    })
                );
            }, DEBOUNCE_DELAY, false);

            this.editorAjaxClient = (method, url, d, successCallback, errorCallback) => {
                console.log("Ajax: " + method + ", " + url);
                const output = {data: []};
                if (d.action === 'create') {
                    console.error("All use cases that crete rows should manifest an editor refresh");
                } else if (d.action === 'edit') {
                    // Update each edited item with the data submitted
                    each(d.data, function (id, value) {
                        let clientState = this._files[id];
                        if (clientState.isEditable()) {
                            clientState.applyEdits(value);
                        }
                        output.data.push(clientState);
                    }, this);
                } else if (d.action === 'remove') {
                    // Remove items from the object
                    each(d.data, function (id, _) {
                        const toDelete = this._files[id];
                        delete this._files[id];
                        this._emitter.emitEvent(EVENT_DATA_ENTRY_DROPPED, [toDelete]);
                    }, this);
                } else {
                    alert("Unreachable code reached: " + d.action);
                }

                // Store latest `this._files` object for next reload
                this._commitLocalStorage();

                // Show Editor what has changed--there is no need to support a separate event on state changes
                // unless we split persistence out to a separate component or had another stakeholder aside from
                // the editor table to keep in sync.
                successCallback(output);
            };
        }

        UploadConfigStore.prototype = {
            initialize: function initialize() {
                if (this._initialized) {
                    throw "Already Initialized";
                }

                // Create or reload client upload state tracking from localStorage entry
                this._files = {};
                const serializedState = localStorage.getItem('client_upload_state');
                if (serializedState) {
                    let {envelope, payload} = JSON.parse(serializedState);
                    if (!!envelope) {
                        const {savedAtVersion} = envelope;
                        const bestMatch = this._supportedVersions.find(registryItem => {
                            // TODO: Use browserify to make semver library accessible.  String comparsion
                            //       will inevitably fail to produce the correct result eventually!!
                            // if (! semver.lt(savedAtVersion, registryItem.from)) {
                            return (savedAtVersion >= registryItem.from);
                        });
                        console.log("Bootstrapping saved data with handler from " + bestMatch.from);
                        bestMatch.handler(envelope, payload);
                    } else {
                        console.warn("Discarding saved data that predates versioning: " + serializedState);
                    }
                } else {
                    console.log("Initializing saved state on first use.");
                    this._commitLocalStorage();
                }

                this._emitter.addListener(EVENT_UPLOAD_TASK_SUCCEEDED, this._commitLocalStorage);
                this._emitter.addListener(EVENT_UPLOAD_TASK_FAILED, this._commitLocalStorage);
                this._emitter.addListener(EVENT_UPLOAD_TASK_DELETED, this._commitLocalStorage);
                this._emitter.addListener(EVENT_DATA_ENTRY_ADDED, this._commitLocalStorage);
                // These cases come about through editorAjaxClient() and are saved there.
                // -- This catches updates that do not change form status, whereas the event
                //    for updates only fired when form completion changes.
                // this._emitter.addListener(EVENT_DATA_ENTRY_UPDATED, this._commitLocalStorage);
                // this._emitter.addListener(EVENT_DATA_ENTRY_DROPPED, this._commitLocalStorage);

                if (Object.values(this._files).some((x) => x.isReportable())) {
                    this._activeView = VIEW_PROGRESS_REPORT;
                } else {
                    this._activeView = VIEW_DATA_ENTRY;
                }

                this._initialized = true;
            },

            /**
             * Examine files dropped by a user to determine if they should be accepted as new, accepted
             * to replace a file already in the workspace, or rejected as duplicates of a file already
             * in the upload queue.  If any submitted files are accepted, fire an event so an active
             * editor may collect the form input required to send them onward.``
             *
             * @param candidateList Collection of File objects as received by UploadDropZoneController.
             */
            _processCandidates: function _processCandidates(candidateList) {
                let file;
                // let acceptedAny = false;
                for (file of candidateList) {
                    const local_key = this.deriveLocalIdentity(file);
                    const doc_file = displayNameForFile(file);
                    if (!ACCEPTED_SUFFIXES.some((suffix) => doc_file.endsWith(suffix))) {
                        console.warn(`${doc_file} does not end with a supported file suffix, skipping!`);
                        continue;
                    } else if (local_key in this._files) {
                        const existing = this._files[local_key];
                        if ((!existing._file) || (existing._metadata._status_message === STATE_FAILED)) {
                            existing.recoverFile(file);
                        } else {
                            const duplicateKey = local_key + Date.now();
                            this._files[duplicateKey] = new UploadableArchive(
                                duplicateKey, this._emitter, null,
                                {doc_file: doc_file, _status_message: STATE_DUPLICATE},
                            )
                            this._emitter.emitEvent(
                                EVENT_DATA_ENTRY_DUPLICATED, [this._files[duplicateKey]]
                            )
                        }
                    } else {
                        this._files[local_key] = new UploadableArchive(
                            local_key, this._emitter, file,
                            {doc_file: doc_file, _status_message: STATE_NEW},
                            this._csrfUrl, this._batchUploadUrl
                        );
                        this._files[local_key].checkFormCompletion();
                    }

                    // acceptedAny = true;
                }
                // if (acceptedAny) {
                //     this._emitter.emitEvent(EVENT_DATA_ENTRY_ADDED, [this])
                // }
                // this._toDataEntryView();
            },

            lookupArchive: function lookupArchive(data) {
                if (!data) {
                    throw "data argument must be defined object or string!";
                } else if ((typeof data === 'object') && !!(data._local_key)) {
                    return this._files[data._local_key];
                } else if (typeof data === 'string') {
                    return this._files[data];
                }

                throw `${data} does not satisfy criteria of an object lookup identifier`;
            },

            sendFinalAck: function sendFinalAck(item) {
                if (!item) {
                    throw "Item must be defined and have a local key";
                }
                const local_key = item._local_key;
                delete this._files[local_key];
                localStorage.removeItem("failMeta/" + local_key)
                localStorage.removeItem("passMeta/" + local_key)

                this._emitter.emitEvent(EVENT_UPLOAD_TASK_DELETED, [item]);
            },

            getActiveView: function getActiveView() {
                return this._activeView;
            },

            deriveLocalIdentity: function deriveLocalIdentity(file) {
                const doc_file = file.fileName || file.name;
                return `${file.size}-${doc_file.replace(/[^0-9a-zA-Z-_]/img, '_')}`;
            },

            _toDataEntryView: function _toDataEntryView() {
                if (this._activeView === VIEW_PROGRESS_REPORT) {
                    this._activeView = VIEW_DATA_ENTRY;
                    this._emitter.emitEvent(EVENT_TOGGLE_OFF_REPORT_VIEW, []);
                }
            },

            _toProgressReportView: function _toProgressReportView() {
                if (this._activeView === VIEW_DATA_ENTRY) {
                    this._activeView = VIEW_PROGRESS_REPORT;
                    this._emitter.emitEvent(EVENT_TOGGLE_OFF_ENTRY_VIEW, []);
                }
            }
        };

        /**
         * An class capturing all the semantics of a single upload task.  It models data entry
         * properties we expose through the DataTables editor and provides a library of utility
         * methods to protect us from having to interact with this object in terms of low
         * level data property access.
         *
         * For example, checkForCompletion() encapsulates a scan through all user-provided data
         * fields to reach a conclusion as to whether or not the form state those fields are a
         * part of is complete or not, applyEdits() checks if the object is in a state where users
         * are allowed to change it and applies the requested changes only if appropriate.
         *
         * DataTables will occasionally turn instances of this class into plain Javascript objects.
         * All of its methods have been defined as methods on an prototype object.  When DataTables
         * returns an instance as a plain javascript object, we would have to construct a new object
         * in order to get back to an instance of this class.  Because all of this class's semantics
         * are defined in methods on its prototype, it is also possible to simply re-assign the
         * prototype any time DataTables has returned a plain object.  The resulting object will
         * acquire all the methods by prototypical inheritance.  It will still not be an instance of
         * UploadableArchive anymore, but it will have all the behavior and that behavior is what we
         * care about consolidating here.
         *
         * In addition to durable used-defined state, this class capture a state machine that models
         * how the behavior of each row changes as it progresses through this workflow.  This state
         * affects the Editor, but is not manipulated directly by the editor, but rather bu actor
         * elements that respond to changes made through the editor and other controllers (e.g.
         * the upload worker and new file dropzone).
         *
         * @param local_key
         * @param emitter
         * @param file
         * @param metadata
         * @constructor
         */
        function UploadableArchive(
            local_key, emitter, file = undefined, metadata = {}, csrfUrl = '', batchUploadUrl = ''
        ) {
            if (!local_key) {
                throw "Local_key argument is mandatory"
            }
            this._local_key = local_key;
            this._emitter = emitter;
            this._file = file;
            this._metadata = Object.keys(metadata)
                .filter(key => ALL_METADATA_PROPS.has(key) && metadata[key])
                .reduce((obj2, key) => (obj2[key] = metadata[key], obj2), {...METADATA_DEFAULTS});
            this._metadata[PROP_LOCAL_KEY] = local_key;
            this._csrfUrl = csrfUrl;
            this._batchUploadUrl = batchUploadUrl;
        }

        UploadableArchive.prototype = {
            /**
             * Method to be used when acting as a server receiving state updated from the table editor to apply
             * changes to stored user data.
             *
             * @param metadata_patch A partial (or complete) set of modified user metadata fields.
             */
            applyEdits: function (metadata_patch) {
                if (metadata_patch && this.isEditable()) {
                    if (metadata_patch._metadata) {
                        const patch = metadata_patch._metadata
                        this._metadata = Object.keys(patch)
                            .filter(key => USER_METADATA_PROPS.has(key) && patch[key])
                            .reduce((obj2, key) => (obj2[key] = patch[key], obj2), this._metadata);
                    } else {
                        this._metadata = Object.keys(metadata_patch)
                            .filter(key => USER_METADATA_PROPS.has(key) && metadata_patch[key])
                            .reduce((obj2, key) => (obj2[key] = metadata_patch[key], obj2), this._metadata);
                    }

                    this.checkFormCompletion()
                }
            },

            /**
             * If a row is in the pre-upload editable state, use this method to determine whether it form
             * fields are complete or not.  An edittable row's _status_message will be set to either
             * STATE_READY or STATE_INCOMPLETE on return from this method.
             */
            checkFormCompletion: function () {
                const meta = this._metadata;
                if (this.isEditable() || (this.isLost() && !!this._file)) {
                    const existing_status = this._metadata._status_message;
                    if (meta.doc_file && meta.name && meta.site_name &&
                        meta.archive_identifier && meta.is_known_good &&
                        (meta.doc_file.length > 0) && (meta.name.length > 0) && (meta.site_name.length > 0) &&
                        (meta.archive_identifier.length > 0) && (['K', 'T', 'F'].includes(meta.is_known_good)) &&
                        (!meta.taser_ticket_number || (parseInt(meta.taser_ticket_number) >= 0))) {
                        meta._status_message = STATE_READY;
                    } else {
                        meta._status_message = STATE_INCOMPLETE;
                    }

                    // NOTE: This intentionally only emits updates if they caused a status change
                    if (this._metadata._status_message !== existing_status) {
                        if (existing_status === STATE_LOST) {
                            this._emitter.emitEvent(EVENT_DATA_ENTRY_RECOVERED, [this]);
                        } else if (existing_status === STATE_NEW) {
                            this._emitter.emitEvent(EVENT_DATA_ENTRY_ADDED, [this]);
                        } else {
                            this._emitter.emitEvent(EVENT_DATA_ENTRY_UPDATED, [this]);
                        }
                    }
                }
            },

            recoverFile: function (file) {
                this._file = file;
                this._metadata.doc_file = displayNameForFile(file)

                if (
                    (this._metadata._status_message === STATE_FAILED_LOST) ||
                    (this._metadata._status_message === STATE_READY_LOST)
                ) {
                    this._metadata._status_message = STATE_FAILED;
                    this._emitter.emitEvent(EVENT_UPLOAD_TASK_RECOVERED, [this]);
                    this.enqueueForUpload();
                } else {
                    this.checkFormCompletion();
                }
            },

            isLost: function isLost() {
                return LOST_FORM_STATES.has(this._metadata._status_message);
            },

            isDuplicate: function isDuplicate() {
                return this._metadata._status_message === STATE_DUPLICATE;
            },

            isEditable: function isEditable() {
                return EDITABLE_FORM_STATES.has(this._metadata._status_message);
            },

            isDataEntry: function isDataEntry() {
                return DATA_ENTRY_FORM_STATES.has(this._metadata._status_message);
            },

            isReportable: function isReportable() {
                return PROGRESS_VIEW_STATES.has(this._metadata._status_message);
            },

            isAcknowledgable: function isAcknowledgable() {
                return DELETE_QUICKLY_STATES.has(this._metadata._status_message)
            },

            isSuccessfulUpload: function isSuccessfulUpload() {
                return this._metadata._status_message === STATE_UPLOADED;
            },

            isUploadReady: function isUploadReady() {
                return this._metadata._status_message === STATE_READY;
            },

            isRetryReady: function isRetryReady() {
                return this._metadata._status_message === STATE_FAILED;
            },

            enqueueForUpload: function enqueueForUpload() {
                if (this._metadata._status_message === STATE_READY) {
                    this._metadata._status_message = STATE_IN_QUEUE;
                    this._emitter.emitEvent(EVENT_DATA_ENTRY_TO_UPLOAD_TASK, [this])
                } else if (this._metadata._status_message === STATE_FAILED) {
                    this._metadata._status_message = STATE_IN_QUEUE;
                    this._emitter.emitEvent(EVENT_UPLOAD_TASK_RETRIED, [this])
                } else {
                    return false;
                }
                return true;
            },

            isInUploadQueue: function isInUploadQueue() {
                return this._metadata._status_message === STATE_IN_QUEUE;
            },

            isUploadInFlight: function isUploadInFlight() {
                return this._metadata._status_message === STATE_IN_FLIGHT;
            },

            abortXhrUpload: function abortXhrUpload() {
                if (!!this._myXhr) {
                    this._myXhr.abort()
                }
                if (!!this._csrfXhr) {
                    this._csrfXhr.abort();
                }
            },

            /**
             * Acquire CSRF tokens in a loop and iteratively POST multipart forms to complete the batch
             * upload task.  Fire an appropriate event to signal completion, whether successful or failed.
             *
             * @returns
             */
            launchUploadFlight: function () {
                if (!this._file) {
                    console.error("Cannot upload an aborted request.  Please acknowledge and dismiss");
                    this._metadata._status_message = STATE_FAILED_LOST;
                    this._emitter.emitEvent(EVENT_UPLOAD_TASK_FAILED, [this]);
                    return;
                } else if (this._metadata._status_message !== STATE_IN_QUEUE) {
                    console.error("launchUploadFlight() called on a task not marked as being in queue: " + this._metadata)
                    this._metadata._status_message = STATE_FAILED;
                    this._emitter.emitEvent(EVENT_UPLOAD_TASK_FAILED, [this]);
                    return;
                }

                this._myXhr = new XMLHttpRequest();
                this._myXhr.timeout = 3600000;
                this._csrfXhr = new XMLHttpRequest();
                this._csrfXhr.timeout = 150000;
                this._metadata._status_message = STATE_IN_FLIGHT;
                this._emitter.emitEvent(EVENT_UPLOAD_TASK_IN_FLIGHT, [this]);

                // First, get a CSRF token to work with.
                const self = this;
                this._csrfXhr.onreadystatechange = () => {
                    if (this._csrfXhr.readyState === 4) {
                        if (this._csrfXhr.status !== 200) {
                            console.error(this._csrfXhr.status + " on CSRF Token Pull")
                            self._metadata._status_message = STATE_FAILED;
                            self._emitter.emitEvent(EVENT_UPLOAD_TASK_FAILED, [self]);
                            localStorage.setItem(
                                `failMeta/${self._local_key}`,
                                JSON.stringify({
                                    'eventClock': Date.now(),
                                    'failedAt': 'csrf',
                                    'timedOut': false,
                                    'timeout': 150000,
                                    'readyState': this._csrfXhr.readyState,
                                    'status': this._csrfXhr.status,
                                    'body': this._csrfXhr.response,
                                    'url': this._csrfXhr.responseURL,
                                    'scenario': 1
                                })
                            );
                        } else {
                            const csrfToken = $(this._csrfXhr.response)[3].value;
                            const fd = new FormData();
                            this._myXhr.onreadystatechange = () => {
                                if (this._myXhr.readyState === 4) {
                                    if (this._myXhr.status === 200) {
                                        const message_payload = JSON.parse(this._myXhr.response);
                                        if (message_payload.status === "success") {
                                            self._metadata.archive_type = message_payload.archive_type;
                                            self._metadata._status_message = STATE_UPLOADED;
                                            self._emitter.emitEvent(EVENT_UPLOAD_TASK_SUCCEEDED, [self]);
                                            localStorage.setItem(
                                                `passMeta/${self._local_key}`,
                                                JSON.stringify({
                                                    'eventClock': Date.now(),
                                                    'messagePayload': message_payload
                                                })
                                            );
                                        } else {
                                            console.error("Upload attempt for " + self._local_key + " fails with " + message_payload);
                                            self._metadata._status_message = STATE_FAILED;
                                            self._emitter.emitEvent(EVENT_UPLOAD_TASK_FAILED, [self]);
                                            localStorage.setItem(
                                                `failMeta/${self._local_key}`,
                                                JSON.stringify({
                                                    'eventClock': Date.now(),
                                                    'failedAt': 'upload',
                                                    'timedOut': false,
                                                    'timeout': 3600000,
                                                    'readyState': this._myXhr.readyState,
                                                    'status': this._myXhr.status,
                                                    'body': this._myXhr.response,
                                                    'url': this._myXhr.responseURL,
                                                    'scenario': 2
                                                })
                                            );
                                        }
                                    } else {
                                        console.error(this._myXhr.status + " on upload attempt: " + this._myXhr.response);
                                        self._metadata._status_message = STATE_FAILED;
                                        self._emitter.emitEvent(EVENT_UPLOAD_TASK_FAILED, [self]);
                                        localStorage.setItem(
                                            `failMeta/${self._local_key}`,
                                            JSON.stringify({
                                                'eventClock': Date.now(),
                                                'failedAt': 'upload',
                                                'timedOut': false,
                                                'timeout': 3600000,
                                                'readyState': this._myXhr.readyState,
                                                'status': this._myXhr.status,
                                                'body': this._myXhr.response,
                                                'url': this._myXhr.responseURL,
                                                'scenario': 3
                                            })
                                        );
                                    }
                                }
                            }
                            this._myXhr.ontimeout = (err) => {
                                console.error("Timeout");
                                self._metadata._status_message = STATE_FAILED;
                                self._emitter.emitEvent(EVENT_UPLOAD_TASK_FAILED, [self]);
                                localStorage.setItem(
                                    `failMeta/${self._local_key}`,
                                    JSON.stringify({
                                        'eventClock': Date.now(),
                                        'failedAt': 'upload',
                                        'timedOut': true,
                                        'timeout': 3600000,
                                        'readyState': this._myXhr.readyState,
                                        'status': this._myXhr.status,
                                        'body': this._myXhr.response,
                                        'url': this._myXhr.responseURL,
                                        'scenario': 4
                                    })
                                );
                            }
                            const meta = this._metadata;
                            fd.set('csrfmiddlewaretoken', csrfToken);
                            fd.set(PROP_DOC_FILE, this._file);
                            fd.set(PROP_NAME, meta.name);
                            fd.set(PROP_SITE, meta.site_name);
                            fd.set(PROP_LABEL, meta.archive_identifier);
                            if (!!meta.taser_ticket_number) {
                                if (parseInt(meta.taser_ticket_number) > 0) {
                                    fd.set(PROP_TASER_TICKET_NUMBER, meta.taser_ticket_number)
                                }
                            }
                            fd.set(PROP_IS_KNOWN_GOOD, meta.is_known_good);
                            // fd.setRequestHeader( 'Cookie', 'Blah' );
                            // Initiate a multipart/form-data upload
                            this._myXhr.open("POST", this._batchUploadUrl, true);
                            this._myXhr.send(fd);
                        }
                    }
                }
                this._csrfXhr.ontimeout = (err) => {
                    console.error('CSRF Timeout');
                    self._metadata._status_message = STATE_FAILED;
                    self._metadata._emitter.emitEvent(EVENT_UPLOAD_TASK_FAILED, [self]);
                    localStorage.setItem(
                        `failMeta/${self._local_key}`,
                        JSON.stringify({
                            'eventClock': Date.now(),
                            'failedAt': 'csrf',
                            'timedOut': true,
                            'timeout': 150000,
                            'readyState': this._csrfXhr.readyState,
                            'status': this._csrfXhr.status,
                            'body': this._csrfXhr.response,
                            'url': this._csrfXhr.responseURL,
                            'scenario': 5
                        })
                    );
                }
                this._csrfXhr.open("GET", this._csrfUrl, true);
                this._csrfXhr.send();
            }
        }

        function UploadViewToggleController(emitter, store, dataEntrySelector, progressSelector) {
            this._emitter = emitter;
            this._store = store;
            this._dataEntryToggle = $(dataEntrySelector);
            this._progressToggle = $(progressSelector);
            this._dataEntryCounter = 0;
            this._progressCounter = 0;

            this._fireDataEntryView = (e) => {
                preventEvent(e);
                this._store._toDataEntryView();
                return false;
            }

            this._fireProgressView = (e) => {
                preventEvent(e);
                this._store._toProgressReportView();
                return false;
            }

            this._onToggleOffDataEntry = () => {
                this._dataEntryToggle.removeClass("active");
                this._dataEntryToggle.removeClass("btn-primary");
                this._dataEntryToggle.addClass("btn-default");
                this._emitter.removeListener(EVENT_UPLOAD_TASK_FAILED, this._bumpProgressCounter);
                this._emitter.removeListener(EVENT_UPLOAD_TASK_SUCCEEDED, this._bumpProgressCounter);
                this._emitter.removeListener(EVENT_UPLOAD_TASK_RECOVERED, this._bumpProgressCounter);
                this._emitter.removeListener(EVENT_DATA_ENTRY_RECOVERED, this._bumpProgressCounter);
                this._emitter.removeListener(EVENT_DATA_ENTRY_TO_UPLOAD_TASK, this._bumpProgressCounter);
            }

            this._onToggleOffProgress = () => {
                this._progressToggle.removeClass("active");
                this._progressToggle.removeClass("btn-primary");
                this._progressToggle.addClass("btn-default");
                this._emitter.removeListener(EVENT_DATA_ENTRY_ADDED, this._bumpDataEntryCounter);
                this._emitter.removeListener(EVENT_DATA_ENTRY_UPDATED, this._bumpDataEntryCounter);
                this._emitter.removeListener(EVENT_DATA_ENTRY_DROPPED, this._bumpDataEntryCounter);
                this._emitter.removeListener(EVENT_DATA_ENTRY_DUPLICATED, this._bumpDataEntryCounter);
                this._emitter.removeListener(EVENT_DATA_ENTRY_RECOVERED, this._bumpDataEntryCounter);
                this._emitter.removeListener(EVENT_DATA_ENTRY_TO_UPLOAD_TASK, this._bumpDataEntryCounter);
            }

            this._onToggleOnDataEntry = () => {
                this._dataEntryToggle.addClass("active");
                this._dataEntryToggle.addClass("btn-primary");
                this._dataEntryToggle.removeClass("btn-default");
                this._dataEntryToggle.contents().replaceWith('Data Entry');
                this._dataEntryCounter = 0;

                // this._emitter.addListener(EVENT_UPLOAD_TASK_IN_FLIGHT, this._bumpProgressCounter);
                this._emitter.addListener(EVENT_UPLOAD_TASK_FAILED, this._bumpProgressCounter);
                this._emitter.addListener(EVENT_UPLOAD_TASK_SUCCEEDED, this._bumpProgressCounter);
                this._emitter.addListener(EVENT_UPLOAD_TASK_RECOVERED, this._bumpProgressCounter);
                this._emitter.addListener(EVENT_DATA_ENTRY_RECOVERED, this._bumpProgressCounter);
                this._emitter.addListener(EVENT_DATA_ENTRY_TO_UPLOAD_TASK, this._bumpProgressCounter);
            }

            this._onToggleOnProgress = () => {
                this._progressToggle.addClass("active");
                this._progressToggle.addClass("btn-primary");
                this._progressToggle.removeClass("btn-default");
                this._progressToggle.contents().replaceWith('Progress Report');
                this._progresCounter = 0;

                this._emitter.addListener(EVENT_DATA_ENTRY_ADDED, this._bumpDataEntryCounter);
                this._emitter.addListener(EVENT_DATA_ENTRY_UPDATED, this._bumpDataEntryCounter);
                this._emitter.addListener(EVENT_DATA_ENTRY_DROPPED, this._bumpDataEntryCounter);
                this._emitter.addListener(EVENT_DATA_ENTRY_DUPLICATED, this._bumpDataEntryCounter);
                this._emitter.addListener(EVENT_DATA_ENTRY_RECOVERED, this._bumpDataEntryCounter);
                this._emitter.addListener(EVENT_DATA_ENTRY_TO_UPLOAD_TASK, this._bumpDataEntryCounter);
            }

            this._bumpDataEntryCounter = () => {
                this._dataEntryCounter += 1;
                this._dataEntryToggle.contents().replaceWith(
                    `<span>Data Entry&nbsp;&nbsp;<span class="badge">${this._dataEntryCounter}</span></span>`
                );
            }

            this._bumpProgressCounter = () => {
                this._progressCounter += 1;
                this._progressToggle.contents().replaceWith(
                    `<span>Progress Report&nbsp;&nbsp;<span class="badge">${this._progressCounter}</span></span>`
                );
            }
        }

        UploadViewToggleController.prototype = {
            initialize: function initialize() {
                if (this._initialized) {
                    throw "Already Initialized";
                }

                this._dataEntryToggle.on('click', '', '', this._fireDataEntryView);
                this._progressToggle.on('click', '', '', this._fireProgressView);

                this._emitter.addListener(EVENT_TOGGLE_OFF_ENTRY_VIEW, this._onToggleOffDataEntry);
                this._emitter.addListener(EVENT_TOGGLE_OFF_REPORT_VIEW, this._onToggleOffProgress);
                this._emitter.addListener(EVENT_TOGGLE_ON_ENTRY_VIEW, this._onToggleOnDataEntry);
                this._emitter.addListener(EVENT_TOGGLE_ON_REPORT_VIEW, this._onToggleOnProgress);
                // this._emitter.addListener(EVENT_ENTRY_EVENT_COUNT_UPDATED, this._onEntryCounterUpdated);
                // this._emitter.addListener(EVENT_REPORT_EVENT_COUNT_UPDATED, this._onReportCounterUpdated);

                if ( this._store.getActiveView() === VIEW_DATA_ENTRY) {
                    this._onToggleOffDataEntry();
                    this._onToggleOnProgress();
                    this._onToggleOffProgress();
                    this._onToggleOnDataEntry();
                } else {
                    this._onToggleOffProgress();
                    this._onToggleOnDataEntry();
                    this._onToggleOffDataEntry();
                    this._onToggleOnProgress();
                }
                this._initialized = true;
            },
        };

        function SubmitterNameController(emitter) {
            // TODO
        }

        function UploadDropZoneController(
            emitter, configStore, dropZoneSelector, dataEntrySelector, progressReportSelector
        ) {
            this._emitter = emitter;
            this._configStore = configStore;
            this._dropZoneSelector = $(dropZoneSelector)
            this._dataEntrySelector = dataEntrySelector
            this._progressReportSelector = progressReportSelector
            this._dataEntryContent = $(dataEntrySelector)
            this._progressReportContent = $(progressReportSelector)
            this._initialized = false;

            this._onDataEntryActive = () => {
                this._progressReportContent.hide();
                this._dataEntryContent.show()
            }

            this._onProgressReportActive = () => {
                this._dataEntryContent.hide()
                this._progressReportContent.show();
            }
        }

        const preventEvent = function (event) {
            event.preventDefault();
        };

        UploadDropZoneController.prototype = {
            initialize: function initialize() {
                if (this._initialized) {
                    throw "Already initialized"
                }

                this._dataEntryContent.hide();
                this._progressReportContent.hide();
                this._emitter.addListener(EVENT_TOGGLE_ON_ENTRY_VIEW, this._onDataEntryActive);
                this._emitter.addListener(EVENT_TOGGLE_ON_REPORT_VIEW, this._onProgressReportActive);

                if (this._configStore.getActiveView() === VIEW_DATA_ENTRY) {
                    this._onDataEntryActive();
                } else {
                    this._onProgressReportActive();
                }


                /**
                 * On drop event
                 * @function
                 * @param {MouseEvent} event
                 */
                const onDrop = (event) => {
                    event.stopPropagation();
                    event.preventDefault();
                    const dataTransfer = event.dataTransfer;
                    if (dataTransfer.items && dataTransfer.items[0] &&
                        dataTransfer.items[0].webkitGetAsEntry) {
                        this.webkitReadDataTransfer(event);
                    } else {
                        this.addFiles(dataTransfer.files);
                    }
                };

                const dropZone = $(this._dropZoneSelector);
                dropZone.on('dragover', null, preventEvent);
                dropZone.on('dragenter', null, preventEvent);
                dropZone.on('drop', null, onDrop);


                this._initialized = true;
            },

            /**
             * Add a HTML5 File object to the list of files.
             * @function
             * @param {FileList|Array} fileList
             */
            addFiles: function addFiles(fileList) {
                const candidates = [];
                each(fileList, (_, file) => {
                    // https://github.com/flowjs/flow.js/issues/55
                    if ((!ie10plus || ie10plus && file.size > 0) && !(file.size % 4096 === 0 && (file.name === '.' || file.fileName === '.'))) {
                        candidates.push(file);
                    }
                }, this);
                this._configStore._processCandidates(candidates);
            },

            /**
             * Read webkit dataTransfer object
             *
             * This method allows drag and drop to support directories, but it will only work
             * in browsers that implement the experimental Webkit Data Transfer API.  It is
             * provided for use where it works, but is not the only entry point to file upload.
             *
             * @see this.addFiles()
             * @function
             * @param event
             */
            webkitReadDataTransfer: function webkitReadDataTransfer(event) {
                const self = this;
                let queue = event.dataTransfer.items.length;
                const files = [];
                each(event.dataTransfer.items, (_, item) => {
                    const entry = item.webkitGetAsEntry();
                    if (!entry) {
                        decrement();
                        return;
                    }
                    if (entry.isFile) {
                        // due to a bug in Chrome's File System API impl - #149735
                        fileReadSuccess(item.getAsFile(), entry.fullPath);
                    } else {
                        readDirectory(entry.createReader());
                    }
                }, this);

                function readDirectory(reader) {
                    reader.readEntries(function (entries) {
                        if (entries.length) {
                            queue += entries.length;
                            each(entries, function (_, entry) {
                                if (entry.isFile) {
                                    const fullPath = entry.fullPath;
                                    entry.file(function (file) {
                                        fileReadSuccess(file, fullPath);
                                    }, readError);
                                } else if (entry.isDirectory) {
                                    readDirectory(entry.createReader());
                                }
                            });
                            readDirectory(reader);
                        } else {
                            decrement();
                        }
                    }, readError);
                }

                function fileReadSuccess(file, fullPath) {
                    // relative path should not start with "/"
                    file.relativePath = fullPath.substring(1);
                    files.push(file);
                    decrement();
                }

                function readError(fileError) {
                    decrement();
                    throw fileError;
                }

                function decrement() {
                    queue = queue - 1
                    if (queue === 0) {
                        // None of these inner methods are bound, but this has been placed in the top-most
                        // closure as `self`, so use self.addFiles() instead of `this.addFiles()
                        self.addFiles(files);
                    }
                }
            },
        };

        function UploadProgressReportController(emitter, tableSelector, store) {
            this._emitter = emitter;
            this._tableSelector = tableSelector;
            this._jqTable = $(tableSelector);
            this._actContainer = $("#action_container_left")
            this._dataTable = undefined
            this._store = store;
            this._initialized = false;

            // There are 5 distinct places where we can log an error during upload processing.
            // Rather than deducing which we hit by examining a series of state flags, each case
            // has a unique index that can be used to jump directly to a handler method for
            // preparing an error report view from the trace data.
            this.errorScenarioReportHandlers = [
                undefined,
                (row_id, errorMeta) => {
                    let message = `Last attempt to upload ${row_id} failed at ${new Date(errorMeta.eventClock)}.<br>`;
                    message += `The CSRF token call failed with HTTP status code ${errorMeta.status}`;
                    showReportIFrame(message, 'danger', undefined, errorMeta.body);
                },
                (row_id, errorMeta) => {
                    let message = `Last attempt to upload ${row_id} failed at ${new Date(errorMeta.eventClock)}.<br>`;
                    message += 'The main upload call returned a 200 OK message body with a controller failure case.';
                    showReportIFrame(message, 'danger', undefined, errorMeta.body);
                },
                (row_id, errorMeta) => {
                    let message = `Last attempt to upload ${row_id} failed at ${new Date(errorMeta.eventClock)}.<br>`;
                    message += `The main upload call failed with HTTP status code ${errorMeta.status}`
                    showReportIFrame(message, 'danger', undefined, errorMeta.body);
                },
                (row_id, errorMeta) => {
                    let message = `Last attempt to upload ${row_id} failed at ${new Date(errorMeta.eventClock)}.<br>`;
                    message += 'The main upload call timed out with no response';
                    showReportIFrame(message, 'danger', undefined, errorMeta.body);
                },
                (row_id, errorMeta) => {
                    let message = `Last attempt to upload ${row_id} failed at ${new Date(errorMeta.eventClock)}.<br>`;
                    message += 'The CSRF token call timed out with no response';
                    showReportIFrame(message, 'danger', undefined, undefined);
                }
            ];

            this._ackAll = () => {
                const storeApi = this._store;
                this._dataTable.rows().every(function () {
                    const data = this.data();
                    const item = storeApi.lookupArchive(data);
                    if (item.isAcknowledgable()) {
                        storeApi.sendFinalAck(item);
                    }
                });
            };

            this._ackSuccessful = () => {
                const storeApi = this._store;
                this._dataTable.rows().every(function () {
                    const data = this.data();
                    const item = storeApi.lookupArchive(data);
                    if (item.isSuccessfulUpload()) {
                        storeApi.sendFinalAck(item);
                    }
                });
            };

            this._ackSelected = () => {
                const storeApi = this._store;
                this._dataTable.rows({selected: true}).every(function () {
                    const data = this.data();
                    const item = storeApi.lookupArchive(data);
                    if (item.isAcknowledgable()) {
                        storeApi.sendFinalAck(item);
                    }
                });
            };

            this._retryAll = () => {
                const storeApi = this._store;
                this._dataTable.rows().every(function () {
                    const data = this.data();
                    const item = storeApi.lookupArchive(data);
                    if (item.isRetryReady()) {
                        item.enqueueForUpload();
                    }
                })
            };

            this._retrySelected = () => {
                const storeApi = this._store;
                this._dataTable.rows({selected: true}).every(function () {
                    const data = this.data();
                    const item = storeApi.lookupArchive(data);
                    if (item.isRetryReady()) {
                        item.enqueueForUpload();
                    }
                })
            };

            this._toggleOffReportView = () => {
                this.deactivate();
                this._emitter.emitEvent(EVENT_TOGGLE_ON_ENTRY_VIEW, []);
            }

            this._toggleOnReportView = () => {
                this.activate();
            }
        }

        UploadProgressReportController.prototype = {
            initialize: function initialize() {
                if (this._initialized) {
                    throw "Already initialized";
                }

                const _onTableDraw = (_settings) => {
                    console.log("Called reporting _onTableDraw()");
                    this._jqTable.DataTable().rows().every(function (a, b, c) {
                        const data = this.data();
                        const node = $(this.node());
                        const status = data._metadata._status_message;
                        if (status === STATE_IN_QUEUE) {
                            node.addClass("text-info");
                        } else if (status === STATE_IN_FLIGHT) {
                            node.addClass("text-primary");
                        } else if (status === STATE_FAILED) {
                            node.addClass("text-danger");
                        } else if (status === STATE_UPLOADED) {
                            node.addClass("text-success");
                        } else if (status === STATE_FAILED_LOST) {
                            node.addClass("text-muted");
                        } else if (status === STATE_READY_LOST) {
                            node.addClass("text-muted");
                        } else if (status === STATE_LOST) {
                            node.addClass("text-muted");
                        }
                    });
                    this._jqTable.DataTable().columns.adjust();
                };

                this._dataTable = this._jqTable.DataTable({
                    ajax: this._store.progressDataLoader,
                    rowId: PROP_LOCAL_KEY,
                    columnDefs: [{
                        orderable: false,
                    }],
                    columns: [
                        {
                            title: "File", name: PROP_DOC_FILE, data: PATH_DOC_FILE,
                            type: "string", render: $.fn.dataTable.render.ellipsis(72)
                        },
                        {
                            title: "Submitter", name: PROP_NAME, data: PATH_NAME, type: "string"
                        },
                        {
                            title: "Site", name: PROP_SITE, data: PATH_SITE, type: "string"
                        },
                        {
                            title: "Archive Label", name: PROP_LABEL, data: PATH_LABEL, type: "string"
                        },
                        {
                            title: "TASER", name: PROP_TASER_TICKET_NUMBER,
                            data: PATH_TASER_TICKET_NUMBER, type: "num",
                            render: (data, type) => {
                                if (type === 'display') {
                                    if (data === "0") {
                                        return '';
                                    }
                                }
                                return data;
                            }
                        },
                        {
                            title: "Known Good?", name: PROP_IS_KNOWN_GOOD,
                            data: PATH_IS_KNOWN_GOOD, type: "string",
                            render: (data, type) => {
                                if (type === 'display') {
                                    if (data in KNOWN_GOOD_OPTIONS_LOOKUP) {
                                        return KNOWN_GOOD_OPTIONS_LOOKUP[data];
                                    }
                                    return KNOWN_GOOD_OPTIONS_LOOKUP['K'];
                                }
                                return data;
                            },
                        },
                        {
                            title: "Status", data: PATH_STATUS_MESSAGE, type: "text",
                            render: (data, type, row) => {
                                if (type === 'display') {
                                    const labelColor = STATE_TO_LABEL_COLOR_MAP[data]
                                    if (!!labelColor) {
                                        return `<span class="label label-${labelColor}">${data}</span>`;
                                    }
                                }
                                return data;
                            }
                        },
                    ],
                    paging: false,
                    ordering: false,
                    info: false,
                    searching: false,
                    scrollY: "calc(50vh - 90px)",
                    drawCallback: _onTableDraw,
                    select: true,
                });

                this._emitter.addListener(EVENT_TOGGLE_OFF_REPORT_VIEW, this._toggleOffReportView);
                this._emitter.addListener(EVENT_TOGGLE_ON_REPORT_VIEW, this._toggleOnReportView);

                const storeApi = this._store;
                const tableApi = this._dataTable;
                const errorScenarioHandlers = this.errorScenarioReportHandlers;
                this._dataTable.on('click', 'tbody td:last-child span', undefined, function onClickBadge(e) {
                    preventEvent(e);
                    const selector = $(this).closest('tr');
                    const row_id = tableApi.row(selector).id();
                    const status = this.textContent;
                    if (e.metaKey || e.altKey || e.shiftKey) {
                        if ((status === STATE_FAILED) || (status === STATE_FAILED_LOST)) {
                            const errorStash = localStorage.getItem("failMeta/" + row_id);
                            if (!errorStash) {
                                console.warn('Sorry, no error stash found for ' + row_id);
                                return false;
                            }

                            const errorMeta = JSON.parse(errorStash);
                            errorScenarioHandlers[errorMeta.scenario](row_id, errorMeta);
                        }
                    }
                    if (status === STATE_UPLOADED) {
                        const passStash = localStorage.getItem("passMeta/" + row_id);
                        if (!passStash) {
                            console.warn('Sorry, no error stash found for ' + row_id);
                            return false;
                        }
                        const passMeta = JSON.parse(passStash);
                        const locationUrl = passMeta.messagePayload.report_url;
                        const message = 'Uploaded successfully at ' + new Date(passMeta.eventClock) + ` as <a href="${location}" target="_blank">${location}</a>.`;
                        const contextColor = 'success';
                        showReportIFrame(message, contextColor, locationUrl, undefined);
                    }
                    if (status === STATE_FAILED) {
                        const item = storeApi.lookupArchive(row_id);
                        if (!item.enqueueForUpload()) {
                            console.warn("Failed to retry retryable upload for " + row_id);
                            return false;
                        }
                    }
                });

                this._dataTableWrapper = $(this._tableSelector + "_wrapper");
                this._dataTableWrapper.hide();
                this._activated = false;
                this._initialized = true;

                if (this._store.getActiveView() === VIEW_PROGRESS_REPORT) {
                    this.activate();
                }
            },

            activate: function activate() {
                if (this._activated) {
                    return;
                }

                this._buttons = new $.fn.dataTable.Buttons(
                    this._dataTable, {
                        buttons: [
                            {
                                name: "acknowledge_collection",
                                extend: "collection",
                                text: "Acknowledge",
                                enabled: true,
                                className: "btn-danger",
                                buttons: [
                                    {
                                        name: 'acknowledge_all',
                                        text: "Acknowledge All",
                                        action: this._ackAll,
                                        enabled: false,
                                    },
                                    {
                                        name: 'acknowledge_success',
                                        text: "Acknowledge Successful",
                                        action: this._ackAll,
                                        enabled: false,
                                    },
                                    {
                                        name: 'acknowledge_selected',
                                        text: "Acknowledge Selected",
                                        action: this._ackSelected,
                                        enabled: false,
                                    }
                                ]
                            },
                            {
                                name: "retry_collection",
                                extend: "collection",
                                text: "Retry",
                                enabled: true,
                                className: "btn-success",
                                buttons: [
                                    {
                                        name: 'retry_all',
                                        text: "Retry All",
                                        action: this._retryAll,
                                        enabled: false,
                                    },
                                    {
                                        name: 'retry_selected',
                                        text: "Retry",
                                        action: this._retrySelected,
                                        enabled: false,
                                    }
                                ],
                            }
                        ],
                        editor: this._editor
                    }
                );
                const buttonContainer = this._buttons.container();
                buttonContainer.appendTo(this._actContainer);
                const ackAllApi = this._dataTable.buttons("acknowledge_all:name");
                const ackSelectedApi = this._dataTable.buttons("acknowledge_selected:name");
                const ackSuccessfulApi = this._dataTable.buttons("acknowledge_successful:name");
                const retryAllApi = this._dataTable.buttons("retry_all:name");
                const retrySelectedApi = this._dataTable.buttons("retry_selected:name");

                const tableApi = this._dataTable;
                const storeApi = this._store;
                this._handleViewUpdateRequired = debounce(function () {
                    tableApi.ajax.reload();
                }, DEBOUNCE_DELAY, false);

                const _enableRelevantButtons = function _enableButtonsIfRelevant() {
                    let ackSelected = false;
                    let retrySelected = false;
                    tableApi.rows({selected: true}).every(function () {
                        const data = this.data();
                        const item = storeApi.lookupArchive(data);
                        if (item.isAcknowledgable()) {
                            ackSelected = true;
                        }
                        if (item.isRetryReady()) {
                            retrySelected = true;
                        }
                    });
                    if (ackSelected) {
                        ackSelectedApi.enable()
                    } else {
                        ackSelectedApi.disable();
                    }
                    if (retrySelected) {
                        retrySelectedApi.enable();
                    } else {
                        retrySelectedApi.disable();
                    }

                    let ackAll = false;
                    let ackSuccess = false;
                    let retryAll = false;
                    tableApi.rows().every(function () {
                        const data = this.data();
                        const item = storeApi.lookupArchive(data);
                        if (item.isAcknowledgable()) {
                            ackAll = true;
                        }
                        if (item.isSuccessfulUpload()) {
                            ackSuccess = true;
                        }
                        if (item.isRetryReady()) {
                            retryAll = true;
                        }
                    });
                    if (ackAll) {
                        ackAllApi.enable()
                    } else {
                        ackAllApi.disable();
                    }
                    if (ackSuccess) {
                        ackSuccessfulApi.enable()
                    } else {
                        ackSuccessfulApi.disable();
                    }
                    if (retryAll) {
                        retryAllApi.enable();
                    } else {
                        retryAllApi.disable();
                    }
                }
                tableApi.on("draw", _enableRelevantButtons);

                this._emitter.addListener(EVENT_DATA_ENTRY_TO_UPLOAD_TASK, this._handleViewUpdateRequired);
                this._emitter.addListener(EVENT_UPLOAD_TASK_RETRIED, this._handleViewUpdateRequired);
                this._emitter.addListener(EVENT_UPLOAD_TASK_DELETED, this._handleViewUpdateRequired);
                this._emitter.addListener(EVENT_UPLOAD_TASK_IN_FLIGHT, this._handleViewUpdateRequired);
                this._emitter.addListener(EVENT_UPLOAD_TASK_SUCCEEDED, this._handleViewUpdateRequired);
                this._emitter.addListener(EVENT_UPLOAD_TASK_FAILED, this._handleViewUpdateRequired);
                this._emitter.addListener(EVENT_UPLOAD_TASK_RECOVERED, this._handleViewUpdateRequired);
                this._emitter.addListener(EVENT_DATA_ENTRY_RECOVERED, this._handleViewUpdateRequired);

                this._dataTable.on(
                    "select", function (e, dt, type, indexes) {
                        if (type === 'row') {
                            tableApi.rows(indexes).every(function (a, b, c) {
                                const data = this.data();
                                const node = $(this.node());
                                const status = data._metadata._status_message;
                                node.removeClass("selected");
                                if (status === STATE_IN_QUEUE) {
                                    node.addClass("bg-info");
                                    node.addClass("text-info");
                                } else if (status === STATE_IN_FLIGHT) {
                                    node.addClass("bg-primary");
                                    node.addClass("text-primary");
                                } else if (status === STATE_FAILED) {
                                    node.addClass("bg-danger");
                                    node.addClass("text-danger");
                                } else if (status === STATE_UPLOADED) {
                                    node.addClass("bg-success");
                                    node.addClass("text-success");
                                } else if (status === STATE_FAILED_LOST) {
                                    node.addClass("bg-danger");
                                    node.addClass("text-danger");
                                } else if (status === STATE_READY_LOST) {
                                    node.addClass("bg-info");
                                    node.addClass("text-info");
                                } else if (status === STATE_LOST) {
                                    node.addClass("bg-warning");
                                    node.addClass("text-warning");
                                }
                            });
                            _enableRelevantButtons();
                        }
                    }
                );

                this._dataTable.on(
                    "deselect", function (e, dt, type, indexes) {
                        if (type === "row") {
                            tableApi.rows(indexes).every(function () {
                                const data = this.data();
                                const node = $(this.node());
                                const status = data._metadata._status_message;
                                if (status === STATE_IN_QUEUE) {
                                    node.removeClass("bg-info");
                                    node.addClass("text-info");
                                } else if (status === STATE_IN_FLIGHT) {
                                    node.removeClass("bg-primary");
                                    node.addClass("text-primary");
                                } else if (status === STATE_FAILED) {
                                    node.removeClass("bg-danger");
                                    node.addClass("text-danger");
                                } else if (status === STATE_UPLOADED) {
                                    node.removeClass("bg-success");
                                    node.addClass("text-success");
                                } else if (status === STATE_FAILED_LOST) {
                                    node.removeClass("bg-danger");
                                    node.removeClass("text-danger");
                                    node.addClass("text-muted");
                                } else if (status === STATE_READY_LOST) {
                                    node.removeClass("bg-info");
                                    node.removeClass("text-info");
                                    node.addClass("text-muted");
                                } else if (status === STATE_LOST) {
                                    node.removeClass("bg-warning");
                                    node.removeClass("text-warning");
                                    node.addClass("text-muted");
                                }
                            });
                            _enableRelevantButtons();
                        }
                    }
                );

                this._dataTableWrapper.show();
                this._dataTable.columns.adjust();
                this._dataTable.ajax.reload();
                this._activated = true;
            },

            deactivate: function deactivate() {
                if (!this._activated) {
                    return;
                }

                this._buttons.destroy();
                console.log("Progress buttons go boom!");

                this._emitter.removeListener(EVENT_DATA_ENTRY_TO_UPLOAD_TASK, this._handleViewUpdateRequired);
                this._emitter.removeListener(EVENT_UPLOAD_TASK_RETRIED, this._handleViewUpdateRequired);
                this._emitter.removeListener(EVENT_UPLOAD_TASK_DELETED, this._handleViewUpdateRequired);
                this._emitter.removeListener(EVENT_UPLOAD_TASK_IN_FLIGHT, this._handleViewUpdateRequired);
                this._emitter.removeListener(EVENT_UPLOAD_TASK_SUCCEEDED, this._handleViewUpdateRequired);
                this._emitter.removeListener(EVENT_UPLOAD_TASK_FAILED, this._handleViewUpdateRequired);
                this._emitter.removeListener(EVENT_UPLOAD_TASK_RECOVERED, this._handleViewUpdateRequired);
                this._emitter.removeListener(EVENT_DATA_ENTRY_RECOVERED, this._handleViewUpdateRequired);

                this._dataTable.off("draw");
                this._dataTable.off("select");
                this._dataTable.off("deselect");
                this._dataTableWrapper.hide();

                this._activated = false;
            },
        };

        function UploadDataEntryController(emitter, tableSelector, store) {
            this._emitter = emitter;
            this._tableSelector = tableSelector;
            this._jqTable = $(tableSelector);
            this._actContainer = $("#action_container_left")
            this._dataTableWrapper = undefined;
            this._dataTable = undefined;
            this._editor = undefined;
            this._store = store;
            this._initialized = false;

            this._uploadSelected = () => {
                const storeApi = this._store;
                this._dataTable.rows({selected: true})
                    .every(function (a, b, c) {
                        const data = this.data();
                        const item = storeApi.lookupArchive(data)
                        // This is both a boolean check and a trigger method--it triggers the
                        // upload and also returns true only if it will trigger the upload, but
                        // that doesn't leave us any reason to check the conditional here...
                        // I know it looks like we're forgetting to check something, so that's
                        // why this explanation is here to explain we haven't.
                        item.enqueueForUpload();
                    });
            };

            this._uploadAll = () => {
                const storeApi = this._store;
                this._dataTable.rows()
                    .every(function (a, b, c) {
                        const data = this.data();
                        const item = storeApi.lookupArchive(data)
                        item.enqueueForUpload();
                    });
            };

            this._removeAll = () => {
                // Must establish a closure to expose elements from this outside the row handler,
                // because DataTables will bind this to a row context object for each row as it iterates
                // and we very much need that context to get at the data and DOM for each row.
                this._editor.remove(
                    this.rows().nodes(), true, {
                        title: 'Delete all rows?',
                        message: 'Do you really want to delete all pending data entry rows?  This cannot be undone!',
                        buttons: 'Confirm delete'
                    }
                ).submit();
            }

            this._removeDuplicates = () => {
                // Must establish a closure to expose elements from this outside the row handler,
                // because DataTables will bind this to a row context object for each row as it iterates
                // and we very much need that context to get at the data and DOM for each row.
                const editorApi = this._editor;
                const storeApi = this._store;
                this._dataTable.rows()
                    .remove(function(idx, data) {
                        const item = storeApi.lookupArchive(data);
                        return item.isDuplicate();
                    }, true, {
                        title: 'Delete all duplicates?',
                        buttons: 'Confirm delete'
                    }).show();
            }

            this._toggleOffEntryView = () => {
                this.deactivate();
                this._emitter.emitEvent(EVENT_TOGGLE_ON_REPORT_VIEW);
            }

            this._toggleOnEntryView = () => {
                this.activate();
            }
        }

        UploadDataEntryController.prototype = {
            initialize: function initialize() {
                if (this._initialized) {
                    throw "Already initialized";
                }

                const jqTable = this._jqTable;
                const _onTableDraw = function (_settings) {
                    console.log("Called _onTableDraw()");
                    jqTable.DataTable()
                        .rows()
                        .every(function (a, b, c) {
                            const data = this.data();
                            const node = $(this.node());
                            const status = data._metadata._status_message;

                            // Replace default styling with color-coded text
                            if (status === STATE_INCOMPLETE) {
                                node.addClass("text-warning");
                            } else if (status === STATE_READY) {
                                node.addClass("text-success");
                            } else if (status === STATE_DUPLICATE) {
                                const fileColumn = node.find("td:first-child");
                                fileColumn.addClass("text-danger");
                                const inputColumns = node.find("td:not(:last-child):not(:first-child)");
                                inputColumns.addClass("blocked");
                                inputColumns.addClass("inactive");
                                inputColumns.addClass("disabled");
                            }
                        });
                    jqTable.DataTable().columns.adjust();
                }

                this._editor = new $.fn.dataTable.Editor({
                    table: this._tableSelector,
                    display: "bootstrap",
                    ajax: this._store.editorAjaxClient,
                    idSrc: PROP_LOCAL_KEY,
                    fields: [
                        {
                            label: "UniqueId",
                            name: PROP_LOCAL_KEY,
                            type: "hidden",
                            multiEditable: false,
                        },
                        {
                            label: "File",
                            name: PATH_DOC_FILE,
                            type: "readonly",
                            multiEditable: false,
                            label_info: "Label Info",
                            field_info: "Field Info",
                        },
                        {
                            label: "Submitter Name",
                            name: PATH_NAME,
                            type: "text",
                            def: "",
                            multiEditable: true,
                            label_info: "Label Info",
                            field_info: "Field Info",
                        },
                        {
                            label: "Site Name",
                            name: PATH_SITE,
                            type: "text",
                            def: "",
                            multiEditable: true,
                            label_info: "Label Info",
                            field_info: "Field Info"
                        },
                        {
                            label: "Archive Label",
                            name: PATH_LABEL,
                            type: "text",
                            def: "",
                            multiEditable: true,
                            label_info: "Label Info",
                            field_info: "Field Info"
                        },
                        {
                            label: "TASER",
                            name: PATH_TASER_TICKET_NUMBER,
                            type: "text",
                            def: null,
                            multiEditable: true,
                            setFormatter: (value, field) => {
                                if ((!value) || (value === "0")) {
                                    return "";
                                }
                                return value;
                            },
                            getFormatter: (value) => {
                                const numeric = parseInt(value);
                                if (numeric > 0) {
                                    return numeric.toString();
                                }
                                return "0";
                            },
                            label_info: "Label Info",
                            field_info: "Field Info"
                        },
                        {
                            label: "Known Good?",
                            name: PATH_IS_KNOWN_GOOD,
                            type: "radio",
                            def: "K",
                            options: KNOWN_GOOD_OPTIONS,
                            multiEditable: true,
                            label_info: "Label Info",
                            field_info: "Field Info"
                        },
                    ],
                    formOptions: {
                        main: {
                            scope: "cell" // Allow multi-row editing with cell selection
                        },
                        inline: {
                            onBlur: "submit"  // Clicking another cell commits current cell rather than
                                              // rolling back changes.
                        }
                    },
                });

                const renderRequired = (label) => {
                    return (data, type, row) => {
                        if (type === "display") {
                            if ((!data) && (row[PROP_STATUS_MESSAGE] !== STATE_DUPLICATE)) {
                                return `<span class="label label-warning">${label}</span>`;
                            }
                        }
                        return data;
                    };
                }

                this._dataTable = this._jqTable.DataTable({
                    ajax: this._store.initialDataLoader,
                    rowId: PROP_LOCAL_KEY,
                    columnDefs: [{
                        orderable: false,
                    }],
                    columns: [
                        {
                            title: "File", name: PROP_DOC_FILE, data: PATH_DOC_FILE,
                            type: "string", render: $.fn.dataTable.render.ellipsis(72)
                        },
                        {
                            title: "Submitter", name: PROP_NAME, data: PATH_NAME,
                            editField: PATH_NAME, type: "string", render: renderRequired("Submitter")
                        },
                        {
                            title: "Site", name: PROP_SITE, data: PATH_SITE,
                            editField: PATH_SITE, type: "string", render: renderRequired("Site")
                        },
                        {
                            title: "Archive Label", name: PROP_LABEL, data: PATH_LABEL,
                            type: "string", editField: PATH_LABEL, render: renderRequired("Label"),
                        },
                        {
                            title: "TASER", name: PROP_TASER_TICKET_NUMBER,
                            data: PATH_TASER_TICKET_NUMBER, type: "num",
                            editField: PATH_TASER_TICKET_NUMBER,
                            render: (data, type) => {
                                if (type === "display") {
                                    if (data === "0") {
                                        return "";
                                    }
                                }

                                return data;
                            }
                        },
                        {
                            title: "Known Good?", name: PROP_IS_KNOWN_GOOD,
                            data: PATH_IS_KNOWN_GOOD, type: "string",
                            editField: PATH_IS_KNOWN_GOOD,
                            render: (data, type) => {
                                if (type === "display") {
                                    if (data in KNOWN_GOOD_OPTIONS_LOOKUP) {
                                        return KNOWN_GOOD_OPTIONS_LOOKUP[data];
                                    }
                                    return KNOWN_GOOD_OPTIONS_LOOKUP["K"];
                                }
                                return data;
                            },
                        },
                        {
                            title: "Status", data: PATH_STATUS_MESSAGE, type: "text",
                            render: (data, type) => {
                                if (type === "display") {
                                    const labelColor = STATE_TO_LABEL_COLOR_MAP[data]
                                    if (!!labelColor) {
                                        return `<span class="label label-${labelColor}">${data}</span>`;
                                    }
                                        return `<span class="label label-default">${data}</span>`;
                                    }
                                return data;
                            }
                        },
                    ],
                    paging: false,
                    ordering: false,
                    info: false,
                    searching: false,
                    scrollY: "calc(50vh - 90px)",
                    drawCallback: _onTableDraw,
                    keys: {
                        columns: [
                            `${PROP_NAME}:name`, `${PROP_SITE}:name`, `${PROP_LABEL}:name`,
                            `${PROP_TASER_TICKET_NUMBER}:name`, `${PROP_IS_KNOWN_GOOD}:name`
                        ],
                        editor: this._editor
                    },
                    select: {
                        items: "row",
                        selector: "tbody tr td:not(:not(:first-child):not(:last-child))",
                        style: "os",
                    },
                    autoFill: {
                        editor: this._editor,
                        focus: "hover",
                        columns: [`${PROP_NAME}:name`, `${PROP_SITE}:name`],
                        horizontal: false,
                        vertical: true
                    },
                });

                // JQ on handlers require closures to get at this state because this is contextually
                // bound to the originating element and cannot be used to 'this instance' cases.
                const storeApi = this._store;
                const editorApi = this._editor;
                const tableApi = this._dataTable;

                // Test for single-cell inline editing
                // Do not use an arrow function because 'this' must be dynamically bound to
                // the DOM node where this event is firing from for the function to work.
                this._onClickHandler = function _onClickHandler(e) {
                    const selector = $(this).closest("tr");
                    const state = tableApi.row(selector).data();
                    const realState = storeApi.lookupArchive(state);
                    if (realState && realState.isEditable()) {
                        editorApi.inline(this);
                        editorApi.enable();
                        return true;
                    }
                    e.preventDefault();
                    editorApi.disable();
                    return false;
                }

                this._onClickStatusHandler = function _onClickStatusHandler(e) {
                    const selector = $(this).closest("tr");
                    const state = tableApi.row(selector).data();
                    const realState = storeApi.lookupArchive(state);
                    if (realState && realState.isUploadReady()) {
                        realState.enqueueForUpload();
                    } else if (realState && realState.isDuplicate()) {
                        storeApi.sendFinalAck(realState);
                    }
                    e.preventDefault();
                    editorApi.disable();
                    return false;
                }

                // Test for multi-cell select-based pop-up editing
                // editorApi.on('preOpen', (e) => {
                //     const modifier = editorApi.modifier();  // Gets the selected row(s) of the table
                //     if (modifier) {
                //         // Variable to flag if the entire selection of rows is editable
                //         const editable = tableApi.rows(modifier).every(function (rowIdx, tableLoop, rowLoop) {
                //             // Get the data for each row and check editability.
                //             const data = this.data();
                //             const realData = storeApi.lookupArchive(data)
                //             return realData.isEditable();
                //         });
                //
                //         if (editable) {
                //             editorApi.enable();
                //         } else {
                //             editorApi.disable();
                //         }
                //     }
                // });
                // this.editorApi.on('preOpen', )

                this._emitter.addListener(EVENT_TOGGLE_OFF_ENTRY_VIEW, this._toggleOffEntryView);
                this._emitter.addListener(EVENT_TOGGLE_ON_ENTRY_VIEW, this._toggleOnEntryView);
                this._dataTable.on("click", "tbody td:not(:first-child):not(:last-child)", this._onClickHandler);
                this._dataTable.on("click", "tbody td:last-child", this._onClickStatusHandler);

                this._dataTableWrapper = $(this._tableSelector + "_wrapper");
                this._dataTableWrapper.hide();
                this._activated = false;
                this._initialized = true;

                if (this._store.getActiveView() === VIEW_DATA_ENTRY) {
                    this.activate();
                }
            },

            activate: function activate() {
                if (this._activated) {
                    return;
                }

                this._buttons = new $.fn.dataTable.Buttons(
                    this._dataTable, {
                        buttons: [
                            {
                                name: "upload_collection",
                                extend: "collection",
                                text: "Upload",
                                enabled: true,
                                className: "btn-primary",
                                buttons: [
                                    {
                                        name: "upload_selected",
                                        text: "Upload Selected",
                                        action: this._uploadSelected,
                                        enabled: false,
                                        className: "btn-default",
                                    },
                                    {
                                        name: "upload_all",
                                        text: "Upload All",
                                        action: this._uploadAll,
                                        enabled: false,
                                        className: "btn-default",
                                    }
                                ]
                            },
                            {
                                name: "delete_collection",
                                extend: "collection",
                                text: "Delete",
                                enabled: true,
                                className: "btn-danger",
                                buttons: [
                                    {
                                        name: "delete_selected",
                                        text: "Drop Selected",
                                        extend: "remove",
                                        enabled: false,
                                        editor: this._editor,
                                        className: "btn-default"
                                    },
                                    {
                                        name: "delete_duplicates",
                                        text: "Drop Duplicates",
                                        action: this._removeDuplicates,
                                        enabled: true,
                                        className: "btn-default"
                                    },
                                    {
                                        name: "delete_all",
                                        text: "Drop All",
                                        action: this._removeAll,
                                        enabled: false,
                                        className: "btn-default",
                                    },
                                ]
                            }, {
                                name: "edit",
                                extend: "edit",
                                editor: this._editor,
                                enabled: true
                            }
                        ],
                        editor: this._editor
                    }
                );
                const buttonsContainer = this._buttons.container();
                buttonsContainer.appendTo(this._actContainer);

                const storeApi = this._store;
                const tableApi = this._dataTable;
                const uploadCollection = tableApi.buttons("upload_collection:name");
                const uploadSelectedButton = uploadCollection.buttons("upload_selected:name");
                const uploadAllButton = uploadCollection.buttons("upload_all:name");
                const deleteCollection = tableApi.buttons("delete_collection:name");
                const deleteSelectedButton = deleteCollection.buttons("delete_selected:name");
                const deleteDuplicatesButton = deleteCollection.buttons("delete_duplicates:name");
                const deleteAllButton = deleteCollection.buttons("delete_all:name");

                this._handleViewUpdateRequired = debounce(function () {
                    tableApi.ajax.reload();
                }, DEBOUNCE_DELAY, false);

                const _enableRelevantButtons = function _enableButtonsIfRelevant() {
                    let uploadSelected = false;
                    let deleteSelected = false;
                    // Delete Selected is available if at least one row is selected.
                    // Upload Selected is available if at least one selected row is Upload Ready.
                    tableApi.rows({selected: true}).every(function (a, b, c) {
                        deleteSelected = true;
                        const data = this.data();
                        const item = storeApi.lookupArchive(data);
                        if (item.isUploadReady()) {
                            uploadSelected = true;
                            // TODO: Is there a way we can abort iteration?  We really
                            //       do not need to look at any more rows once we enter this
                            //       block at least once.
                        }
                    });
                    let deleteAll = false;
                    let deleteDuplicates = false;
                    let uploadAll = false;
                    // Delete All is available if at least one row exists.
                    // Delete Duplicates is available if at least one duplicate exists.
                    // Upload All is available if at least one existing row is Ready.
                    tableApi.rows().every(function (a, b, c) {
                        deleteAll = true;
                        const data = this.data();
                        const item = storeApi.lookupArchive(data);
                        if (item.isUploadReady()) {
                            uploadAll = true;
                        }
                        if (item.isDuplicate()) {
                            deleteDuplicates = true;
                        }
                    });
                    if (uploadSelected) {
                        uploadSelectedButton.enable();
                    } else {
                        uploadSelectedButton.disable();
                    }
                    if (uploadAll) {
                        uploadAllButton.enable();
                    } else {
                        uploadAllButton.disable();
                    }
                    if (deleteDuplicates) {
                        deleteDuplicatesButton.enable();
                    } else {
                        deleteDuplicatesButton.disable();
                    }
                    if (deleteSelected) {
                        deleteSelectedButton.enable();
                    } else {
                        deleteSelectedButton.disable();
                    }
                    if (deleteAll) {
                        deleteAllButton.enable();
                    } else {
                        deleteAllButton.disable();
                    }
                }

                this._dataTable.on("draw", _enableRelevantButtons);

                this._emitter.addListener(EVENT_DATA_ENTRY_ADDED, this._handleViewUpdateRequired);
                this._emitter.addListener(EVENT_DATA_ENTRY_DUPLICATED, this._handleViewUpdateRequired);
                this._emitter.addListener(EVENT_DATA_ENTRY_UPDATED, this._handleViewUpdateRequired);
                this._emitter.addListener(EVENT_DATA_ENTRY_DROPPED, this._handleViewUpdateRequired);
                this._emitter.addListener(EVENT_DATA_ENTRY_RECOVERED, this._handleViewUpdateRequired);
                this._emitter.addListener(EVENT_DATA_ENTRY_TO_UPLOAD_TASK, this._handleViewUpdateRequired);

                /**
                 * Override default select styling with color-coded highlighting matching each file"s form upload
                 * readiness.  Green for completely ready, amber for incomplete form, red for a duplicate upload
                 * that will never go anywhere.
                 */
                this._dataTable.on(
                    "select", function (e, dt, type, indexes) {
                        if (type === "row") {
                            tableApi.rows(indexes).every(function () {
                                const data = this.data();
                                const node = $(this.node());
                                const status = data._metadata._status_message;
                                if (status === STATE_INCOMPLETE) {
                                    node.addClass("text-warning");
                                    node.removeClass("selected");
                                    node.addClass("bg-warning");
                                } else if (status === STATE_READY) {
                                    node.addClass("text-success");
                                    node.removeClass("selected");
                                    node.addClass("bg-success");
                                } else if (status === STATE_DUPLICATE) {
                                    node.find("td:first-child").addClass("text-danger");
                                    node.removeClass("selected");
                                    node.find("td:not(:not(:first-child):not(:last-child))").addClass("bg-danger");
                                }
                            });

                            _enableRelevantButtons();
                        }
                    }
                );

                this._dataTable.on(
                    "deselect", function (e, dt, type, indexes) {
                        if (type === "row") {
                            // Back-out of custom styling and restore baseline custom styling
                            // when stepping back through de-selection.
                            tableApi.rows(indexes).every(function () {
                                const data = this.data();
                                const node = $(this.node());
                                const status = data._metadata._status_message;
                                if (status === STATE_INCOMPLETE) {
                                    node.addClass("text-warning");
                                    node.removeClass("bg-warning");
                                } else if (status === STATE_READY) {
                                    node.addClass("text-success");
                                    node.removeClass("bg-success");
                                } else if (status === STATE_DUPLICATE) {
                                    node.find("td:first-child").addClass("text-danger");
                                    node.removeClass("bg-danger");
                                }
                            });

                            _enableRelevantButtons();
                        }
                    }
                );

                this._dataTableWrapper.show();
                this._dataTable.columns.adjust();
                this._dataTable.ajax.reload();
                this._activated = true;
            },

            deactivate: function deactivate() {
                if (!this._activated) {
                    return;
                }

                this._buttons.destroy();

                this._emitter.removeListener(EVENT_DATA_ENTRY_ADDED, this._handleViewUpdateRequired);
                this._emitter.removeListener(EVENT_DATA_ENTRY_DUPLICATED, this._handleViewUpdateRequired);
                this._emitter.removeListener(EVENT_DATA_ENTRY_UPDATED, this._handleViewUpdateRequired);
                this._emitter.removeListener(EVENT_DATA_ENTRY_DROPPED, this._handleViewUpdateRequired);
                this._emitter.removeListener(EVENT_DATA_ENTRY_RECOVERED, this._handleViewUpdateRequired);
                this._emitter.removeListener(EVENT_DATA_ENTRY_TO_UPLOAD_TASK, this._handleViewUpdateRequired);

                this._dataTable.off("draw");
                this._dataTable.off("select");
                this._dataTable.off("deselect");
                this._dataTableWrapper.hide();

                this._activated = false;
            },
        };

        function UploadClientService(emitter, configStore) {
            this._emitter = emitter;
            this._configStore = configStore
            this._runWaitQueue = [];
            this._uploadsInFlight = {};
            this._incomingQueue = [];
            this._numberInFlight = 0;
            this._initialized = false;
        }

        UploadClientService.prototype = {
            initialize: function initialize() {
                if (this._initialized) {
                    throw "Already initialized!";
                }

                const _handleBeginEvent = () => {
                    if (!this._incomingQueue || this._incomingQueue.length === 0) {
                        console.warn("Begin button was clicked with no tasks ready to enqueue?");
                        this._emitter.emit(EVENT_UPLOAD_QUEUE_IS_EMPTY, []);
                        return;
                    }
                    this._runWaitQueue.reverse();
                    this._runWaitQueue = this._runWaitQueue.concat(this._incomingQueue);
                    this._runWaitQueue.reverse();
                    this._incomingQueue.splice(0, this._incomingQueue.length)
                    this._maybeUploadMore();
                };

                const _debouncedBeginEvent = debounce(_handleBeginEvent, DEBOUNCE_DELAY, false)

                const _handleFileUploadToQueue = (uploadable) => {
                    this._incomingQueue.push(uploadable);
                    _debouncedBeginEvent();
                }

                const _handleFileUploadStopped = (uploadable) => {
                    delete this._uploadsInFlight[uploadable._local_key]
                    this._numberInFlight = this._numberInFlight - 1;
                    this._maybeUploadMore();
                };

                const _handleFileUploadDeleted = (uploadable) => {
                    if (uploadable.isInUploadQueue()) {
                        const idx = this._incomingQueue.indexOf(uploadable);
                        if (idx === 0) {
                            this._incomingQueue.shift();
                        } else if (idx > 0) {
                            this._incomingQueue.splice(idx - 1, 1);
                        } else {
                            // throw new Error(uploadable + " not found to remove from queue?");
                            console.error('Cannot remove ' + uploadable + ' because it is not even in the queue');
                            return false;
                        }
                    } else if (uploadable.isUploadInFlight()) {
                        uploadable.abortXhrUpload();
                        delete this._uploadsInFlight[uploadable._local_key]
                        this._numberInFlight = this._numberInFlight - 1;
                        this._maybeUploadMore();
                    }
                }

                this._emitter.addListener(EVENT_UPLOAD_TASK_SUCCEEDED, _handleFileUploadStopped)
                this._emitter.addListener(EVENT_UPLOAD_TASK_FAILED, _handleFileUploadStopped)
                this._emitter.addListener(EVENT_DATA_ENTRY_TO_UPLOAD_TASK, _handleFileUploadToQueue);
                this._emitter.addListener(EVENT_UPLOAD_TASK_RETRIED, _handleFileUploadToQueue);
                this._emitter.addListener(EVENT_UPLOAD_TASK_DELETED, _handleFileUploadDeleted);
                this._initialized = true;
            },

            _maybeUploadMore: function _maybeUploadMore() {
                while ((this._numberInFlight < MAX_CONCURRENT_UPLOADS) && (this._runWaitQueue.length > 0)) {
                    const nextLaunch = this._runWaitQueue.pop();
                    if (nextLaunch && '_local_key' in nextLaunch) {
                        this._uploadsInFlight[nextLaunch._local_key] = nextLaunch;
                        this._numberInFlight += 1;
                        nextLaunch.launchUploadFlight();
                    }
                }
                if (this._numberInFlight === 0) {
                    this._emitter.emitEvent(EVENT_UPLOAD_QUEUE_IS_EMPTY, []);
                }
            },
        }


        function BatchUploadAppModule(
            inspectorVersion, dropZoneDivSelector,
            dataEntryTableSelector, progressReportTableSelector,
            viewModeDataEntrySelector, viewModeProgressSelector,
            dataEntrySelector, progressReportSelector,
            csrfUrl, batchUploadUrl
        ) {
            this.version = inspectorVersion;

            this._emitter = new EventEmitter();
            this._store = new UploadConfigStore(inspectorVersion, this._emitter, csrfUrl, batchUploadUrl);
            this._viewSelector = new UploadViewToggleController(
                this._emitter, this._store, viewModeDataEntrySelector, viewModeProgressSelector,
            )
            this._editor = new UploadDataEntryController(
                this._emitter, dataEntryTableSelector, this._store);
            this._reporter = new UploadProgressReportController(
                this._emitter, progressReportTableSelector, this._store
            )
            this._dropZone = new UploadDropZoneController(
                this._emitter, this._store, dropZoneDivSelector, dataEntrySelector, progressReportSelector
            );
            this._service = new UploadClientService(this._emitter, this._store);
        }

        BatchUploadAppModule.prototype = {
            /**
             * Main entry routine once all parts are wired.
             * @type {Function}
             */
            start: function start() {
                // Ensure that JQuery knows to include the `dataTransfer` property from drop events or else
                // none of this will function!  This is global configuration and this is s bootstrapping entry
                // point.
                jQuery.event.addProp("dataTransfer");

                // Remove the autofill plugins we do not wish to utilize so there will no longer be a popup
                // to verify our preference.
                delete $.fn.dataTable.AutoFill.actions["increment"]
                delete $.fn.dataTable.AutoFill.actions["fillHorizontal"]
                delete $.fn.dataTable.AutoFill.actions["fill"]

                // Opt in to Bootstrap"s optional tooltips and popovers
                $('[data-toggle="tooltip"]').tooltip()
                $('[data-toggle="popover"]').popover()

                $('a[data-toggle="tab"]').on("shown.bs.tab", function (e) {
                    setTimeout(() => {
                        $.fn.dataTable.tables({visible: true, api: true}).columns.adjust();
                    }, 20);
                });

                this._store.initialize();
                this._dropZone.initialize();
                this._viewSelector.initialize();
                this._editor.initialize();
                this._reporter.initialize();
                this._service.initialize();
            }
        };

        if (typeof module === "object" && module && typeof module.exports === "object") {
            // Expose BulkUploader as module.exports in loaders that implement the Node
            // module pattern (including browserify). Do not create the global, since
            // the user will be storing it themselves locally, and globals are frowned
            // upon in the Node module world.
            module.exports = BatchUploadAppModule;
        } else {
            // Otherwise expose Flow to the global object as usual
            window.BatchUploadAppModule = BatchUploadAppModule;

            // Register as a named AMD module, since Flow can be concatenated with other
            // files that may use define, but not via a proper concatenation script that
            // understands anonymous AMD modules. A named AMD is safest and most robust
            // way to register. Lowercase flow is used because AMD module names are
            // derived from file names, and Flow is normally delivered in a lowercase
            // file name. Do this after creating the global so that if an AMD module wants
            // to call noConflict to hide this version of Flow, it will work.
            if (typeof define === "function" && define.amd) {
                define("batch_upload_app_module", [], function () {
                    return BatchUploadAppModule;
                });
            }
        }
    }
)
(typeof window !== "undefined" && window, typeof document !== "undefined" && document);
