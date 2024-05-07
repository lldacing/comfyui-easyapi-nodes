import { app } from "/scripts/app.js";
import { api } from "/scripts/api.js";
import { debounce } from "./debounce.js"

app.registerExtension({
    name: "Comfy.EasyApi.Setting",
    async setup(app) {
        this.add_history_setting(app);
        // plugins are loaded before the manager, cannot be patched with Python hooks on Windows.
		const systemStats = await api.getSystemStats();
        if (systemStats.system.os !== 'nt') {
            this.add_github_clone_mirror_setting(app);
        }
        this.add_github_mirror_setting(app);
        this.add_rawgithub_mirror_setting(app);
        this.add_huggingface_mirror_setting(app);

        const ctxMenu = LiteGraph.ContextMenu;
		const replace = () => {
			LiteGraph.ContextMenu = function (values, options) {
				options = options || {};
				options.autoopen = true;
				return ctxMenu.call(this, values, options);
			};
			LiteGraph.ContextMenu.prototype = ctxMenu.prototype;
		};
		app.ui.settings.addSetting({
            id: "Easyapi.ContextMenu.autoopen",
            name: "[EasyApi] Auto Open Sub Menu",
            type: "boolean",
            defaultValue: false,
            onChange(value) {
                if (value) {
                    replace(value);
                } else {
                    LiteGraph.ContextMenu = ctxMenu;
                }
            },
        });
        app.ui.settings.addSetting({
            id: "Easyapi.Search.fuzzy",
            name: "[EasyApi] Fuzzy Search",
            type: "boolean",
            defaultValue: false,
            onChange(value) {
                LiteGraph.search_fuzzy_match = value;
            },
        });
    },
    add_history_setting: function (app) {
        const changeFun = debounce((n, o) => api.fetchApi("/easyapi/history/size", {
            method: 'POST',
            headers: {
                "content-type": "application/json",
            },
            body: JSON.stringify({
                maxSize: n
            })
        }), 1000, false)
        app.ui.settings.addSetting({
            id: "Easyapi.SizeOfHistory",
            name: "[EasyApi] Maximum History Size",
            defaultValue: 10000,
            type: "slider",
            attrs: {
                min: 1,
                max: 10000,
                step: 1,
            },
            onChange: (newVal, oldVal) => {
                changeFun.apply(null, [newVal, oldVal])
            }
        });
    },
    add_github_clone_mirror_setting: function (app) {
        const changeFun = debounce((n, o) => api.fetchApi("/easyapi/settings/clone_github_mirror", {
            method: 'POST',
            headers: {
                "content-type": "application/json",
            },
            body: JSON.stringify({
                clone_github_mirror: n
            })
        }), 1000, false)
        app.ui.settings.addSetting({
            id: "Easyapi.MirrorSet.github.clone",
            name: "[EasyApi] Github Clone Mirror",
            defaultValue: "None",
            tooltip: "Will replace host github.com. Suitable of git clone from github.com. On Windows platforms, it is not valid for ComfyUI manager.",
            type: "combo",
            options: [
                {
                    value: "None",
                    text: "None"
                },
                {
                    value: "hub.gitmirror.com/https://github.com",
                    text: "gitmirror.com"
                },
                {
                    value: "mirror.ghproxy.com/https://github.com",
                    text: "mirror.ghproxy.com"
                },
                {
                    value: "ghproxy.net/https://github.com",
                    text: "ghproxy.net"
                },
                {
                    value: "ghproxy.org/https://github.com",
                    text: "ghproxy.org"
                },
                {
                    value: "gh-proxy.com/https://github.com",
                    text: "gh-proxy.com"
                },
                {
                    value: "gh.ddlc.top/https://github.com",
                    text: "gh.ddlc.top"
                },
                {
                    value: "mirrors.chenby.cn/https://github.com",
                    text: "mirrors.chenby.cn"
                },
                {
                    value: "521github.com/extdomains/github.com",
                    text: "521github.com"
                },
                {
                    value: "github.moeyy.xyz/https://github.com",
                    text: "github.moeyy.xyz"
                }
            ],

            onChange: (newVal, oldVal) => {
                changeFun.apply(null, [newVal, oldVal])
            }
        });
    },
    add_github_mirror_setting: function (app) {
        const changeFun = debounce((n, o) => api.fetchApi("/easyapi/settings/github_mirror", {
            method: 'POST',
            headers: {
                "content-type": "application/json",
            },
            body: JSON.stringify({
                github_mirror: n
            })
        }), 1000, false)
        app.ui.settings.addSetting({
            id: "Easyapi.MirrorSet.github",
            name: "[EasyApi] Github Mirror",
            defaultValue: "None",
            tooltip: "Will replace host github.com. Suitable of downloading some models from github.com.",
            type: "combo",
            options: [
                {
                    value: "None",
                    text: "None"
                },
                {
                    value: "hub.gitmirror.com/https://github.com",
                    text: "gitmirror.com"
                },
                {
                    value: "mirror.ghproxy.com/https://github.com",
                    text: "mirror.ghproxy.com"
                },
                {
                    value: "ghproxy.net/https://github.com",
                    text: "ghproxy.net"
                },
                {
                    value: "ghproxy.org/https://github.com",
                    text: "ghproxy.org"
                },
                {
                    value: "gh-proxy.com/https://github.com",
                    text: "gh-proxy.com"
                },
                {
                    value: "gh.ddlc.top/https://github.com",
                    text: "gh.ddlc.top"
                },
                {
                    value: "mirrors.chenby.cn/https://github.com",
                    text: "mirrors.chenby.cn"
                },
                {
                    value: "521github.com/extdomains/github.com",
                    text: "521github.com"
                },
                {
                    value: "github.moeyy.xyz/https://github.com",
                    text: "github.moeyy.xyz"
                }
            ],

            onChange: (newVal, oldVal) => {
                changeFun.apply(null, [newVal, oldVal])
            }
        });
    },
    add_rawgithub_mirror_setting: function (app) {
        const changeFun = debounce((n, o) => api.fetchApi("/easyapi/settings/rawgithub_mirror", {
            method: 'POST',
            headers: {
                "content-type": "application/json",
            },
            body: JSON.stringify({
                rawgithub_mirror: n
            })
        }), 1000, false)
        app.ui.settings.addSetting({
            id: "Easyapi.MirrorSet.rawgithub",
            name: "[EasyApi] RawGithub Mirror",
            defaultValue: "None",
            tooltip: "Will replace host raw.githubusercontent.com",
            type: "combo",
            options: [
                {
                    value: "None",
                    text: "None"
                },
                {
                    value: "raw.gitmirror.com",
                    text: "gitmirror.com"
                },
                {
                    value: "mirror.ghproxy.com/https://raw.githubusercontent.com",
                    text: "mirror.ghproxy.com"
                },
                {
                    value: "ghproxy.net/https://raw.githubusercontent.com",
                    text: "ghproxy.net"
                },
                {
                    value: "ghproxy.org/https://raw.githubusercontent.com",
                    text: "ghproxy.org"
                },
                {
                    value: "gh-proxy.com/https://raw.githubusercontent.com",
                    text: "gh-proxy.com"
                },
                {
                    value: "mirrors.chenby.cn/https://raw.githubusercontent.com",
                    text: "mirrors.chenby.cn"
                },
                {
                    value: "gh.ddlc.top/https://raw.githubusercontent.com",
                    text: "gh.ddlc.top"
                },
                {
                    value: "521github.com/extdomains/raw.githubusercontent.com",
                    text: "521github.com"
                },
                {
                    value: "github.moeyy.xyz/https://raw.githubusercontent.com",
                    text: "github.moeyy.xyz"
                }
            ],

            onChange: (newVal, oldVal) => {
                changeFun.apply(null, [newVal, oldVal])
            }
        });
    },
    add_huggingface_mirror_setting: function (app) {
        const changeFun = debounce((n, o) => api.fetchApi("/easyapi/settings/huggingface_mirror", {
            method: 'POST',
            headers: {
                "content-type": "application/json",
            },
            body: JSON.stringify({
                huggingface_mirror: n
            })
        }), 1000, false)
        app.ui.settings.addSetting({
            id: "Easyapi.MirrorSet.huggingface",
            name: "[EasyApi] Huggingface Mirror",
            tooltip: "Will replace host huggingface.co",
            defaultValue: "None",
            type: "combo",
            options: [
                {
                    value: "None",
                    text: "None"
                },
                {
                    value: "hf-mirror.com",
                    text: "hf-mirror.com"
                },
                // {
                //     value: "gitee.com/hf-models",
                //     text: "gitee.com"
                // }
            ],

            onChange: (newVal, oldVal) => {
                changeFun.apply(null, [newVal, oldVal])
            }
        });
    },
})

app.registerExtension({
    name: "Comfy.EasyApi.Search",
    async init(app) {
		function fuzzy_match_filter(inputStr, str, matchedPos) {
            matchedPos = matchedPos || [];
			let splitStr = inputStr.split("");
			let j = splitStr.shift()
			for (let i in str) {
				if (str[i] == j) {
                    matchedPos.push(i)
                    if (splitStr.length == 0) {
                        return true;
                    }
                    j = splitStr.shift()
				}
			}
			return false;
		}

        function highlight_keywords(oldText, recordPos) {
            let newText = "";
            let pos = recordPos.shift();
            let split = oldText.split("")
            for (let j in split) {
                let c = oldText[j];
                if (j == pos) {
                    newText += "<span style='color: red'>" + c + "</span>";
                    if (recordPos.length > 0) {
                        pos = recordPos.shift();
                    } else {
                        newText += oldText.slice(parseInt(j) + 1);
                        break;
                    }
                } else {
                    newText += c;
                }
            }
            return newText;
        }

		let oldOnSearchBox = app.canvas.onSearchBox
		let oldShowSearchBox = LGraphCanvas.prototype.showSearchBox
        LGraphCanvas.prototype.showSearchBox = function(event, options) {
			let that = this;
			// copy from oldShowSearBox
			let def_options = { slot_from: null
                        ,node_from: null
                        ,node_to: null
                        ,do_type_filter: LiteGraph.search_filter_enabled
                        ,type_filter_in: false                          // these are default: pass to set initially set values
                        ,type_filter_out: false
                        ,show_general_if_none_on_typefilter: true
                        ,show_general_after_typefiltered: true
                        ,hide_on_mouse_leave: LiteGraph.search_hide_on_mouse_leave
                        ,show_all_if_empty: true
                        ,show_all_on_open: LiteGraph.search_show_all_on_open
                        ,search_fuzzy_match: LiteGraph.search_fuzzy_match || false // easyapi custom setting
                    };
			options = Object.assign(def_options, options || {});
            if (!options.search_fuzzy_match) {
                app.canvas.onSearchBox = oldOnSearchBox;
                return oldShowSearchBox?.apply(this, [event, options]);
            }
            let dialog = oldShowSearchBox?.apply(this, [event, options])

			app.canvas.onSearchBox = function (helper, inputStr, graphcanvas) {
				// let options = {}
				var c = 0;
				let str = inputStr.toLowerCase();
				var filter = graphcanvas.filter || graphcanvas.graph.filter;

				// filter by type preprocess
				if (options.do_type_filter && that.search_box) {
					var sIn = that.search_box.querySelector(".slot_in_type_filter");
					var sOut = that.search_box.querySelector(".slot_out_type_filter");
				} else {
					var sIn = false;
					var sOut = false;
				}

				let filtered = [];

				//extras
				for (var i in LiteGraph.searchbox_extras) {
                    var extra = LiteGraph.searchbox_extras[i];
                    if ((!options.show_all_if_empty || str) && !fuzzy_match_filter(str, extra.desc)) {
                        continue;
                    }
                    var ctor = LiteGraph.registered_node_types[ extra.type ];
                    if( ctor && ctor.filter != filter )
                        continue;
                    if( ! inner_test_filter(extra.type) )
                        continue;
                    // addResult( extra.desc, "searchbox_extra" );
					filtered.push(extra.desc)
                    if ( LGraphCanvas.search_limit !== -1 && c++ > LGraphCanvas.search_limit ) {
                        break;
                    }
                }

				let temp_filtered = []
                if (Array.prototype.filter) { //filter supported
                    var keys = Object.keys( LiteGraph.registered_node_types ); //types
                    temp_filtered = keys.filter( inner_test_filter );
                } else {
                    temp_filtered = [];
                    for (var i in LiteGraph.registered_node_types) {
                        if( inner_test_filter(i) )
                            temp_filtered.push(i);
                    }
                }

                for (var i = 0; i < temp_filtered.length; i++) {
                    // addResult(filtered[i]);
					filtered.push(temp_filtered[i]);
                    if ( LGraphCanvas.search_limit !== -1 && c++ > LGraphCanvas.search_limit ) {
                        break;
                    }
                }

                // add general type if filtering
                /*if (options.show_general_after_typefiltered
                    && (sIn.value || sOut.value)
                ){
                    let filtered_extra = [];
                    for (var i in LiteGraph.registered_node_types) {
                        if( inner_test_filter(i, {inTypeOverride: sIn&&sIn.value?"*":false, outTypeOverride: sOut&&sOut.value?"*":false}) )
                            filtered_extra.push(i);
                    }
                    for (var i = 0; i < filtered_extra.length; i++) {
						// addResult(filtered_extra[i], "generic_type");
                        filtered.push(filtered_extra[i]);
						if (LGraphCanvas.search_limit !== -1 && c++ > LGraphCanvas.search_limit) {
							break;
						}
					}
                }*/

                // check il filtering gave no results
                if ((sIn.value || sOut.value) &&
                    ( (helper.childNodes.length == 0 && options.show_general_if_none_on_typefilter) )
                ){
                    var filtered_extra = [];
                    for (var i in LiteGraph.registered_node_types) {
                        if( inner_test_filter(i, {skipFilter: true}) )
                            filtered_extra.push(i);
                    }
                    for (var i = 0; i < filtered_extra.length; i++) {
                        // addResult(filtered_extra[i], "not_in_filter");
                        filtered.push(filtered_extra[i]);
                        if ( LGraphCanvas.search_limit !== -1 && c++ > LGraphCanvas.search_limit ) {
                            break;
                        }
                    }
                }

                function inner_test_filter( type, optsIn )
                {
                    var optsIn = optsIn || {};
                    var optsDef = { skipFilter: false
                                    ,inTypeOverride: false
                                    ,outTypeOverride: false
                                  };
                    var opts = Object.assign(optsDef,optsIn);
                    var ctor = LiteGraph.registered_node_types[ type ];
                    if(filter && ctor.filter != filter )
                        return false;
                    if ((!options.show_all_if_empty || str) && !fuzzy_match_filter(str, type.toLowerCase()) && (!ctor.title || !fuzzy_match_filter(str, ctor.title.toLowerCase())))
                        return false;

                    // filter by slot IN, OUT types
                    if(options.do_type_filter && !opts.skipFilter){
                        var sType = type;

                        var sV = sIn.value;
                        if (opts.inTypeOverride!==false) sV = opts.inTypeOverride;
                        //if (sV.toLowerCase() == "_event_") sV = LiteGraph.EVENT; // -1

                        if(sIn && sV){
                            //console.log("will check filter against "+sV);
                            if (LiteGraph.registered_slot_in_types[sV] && LiteGraph.registered_slot_in_types[sV].nodes){ // type is stored
                                //console.debug("check "+sType+" in "+LiteGraph.registered_slot_in_types[sV].nodes);
                                var doesInc = LiteGraph.registered_slot_in_types[sV].nodes.includes(sType);
                                if (doesInc!==false){
                                    //console.log(sType+" HAS "+sV);
                                }else{
                                    /*console.debug(LiteGraph.registered_slot_in_types[sV]);
                                    console.log(+" DONT includes "+type);*/
                                    return false;
                                }
                            }
                        }

                        var sV = sOut.value;
                        if (opts.outTypeOverride!==false) sV = opts.outTypeOverride;
                        //if (sV.toLowerCase() == "_event_") sV = LiteGraph.EVENT; // -1

                        if(sOut && sV){
                            //console.log("search will check filter against "+sV);
                            if (LiteGraph.registered_slot_out_types[sV] && LiteGraph.registered_slot_out_types[sV].nodes){ // type is stored
                                //console.debug("check "+sType+" in "+LiteGraph.registered_slot_out_types[sV].nodes);
                                var doesInc = LiteGraph.registered_slot_out_types[sV].nodes.includes(sType);
                                if (doesInc!==false){
                                    //console.log(sType+" HAS "+sV);
                                }else{
                                    /*console.debug(LiteGraph.registered_slot_out_types[sV]);
                                    console.log(+" DONT includes "+type);*/
                                    return false;
                                }
                            }
                        }
                    }
                    return true;
                }

                if (helper.dataset["observer"] != "true") {
                    helper.dataset["observer"] = "true";
                    let observConfig = { attributes: false, childList: true };
                    let observer = new MutationObserver(mutations => {
                        for (let i = 0; i < mutations.length; i++) {
                            let mutationRecord = mutations[i];
                            let searchWord = helper.parentNode.querySelector("input").value;
                            if (searchWord.trim().length == 0) {
                                break;
                            }
                            for (let item of mutationRecord.addedNodes) {
                                if (!item.dataset["fuzzy"] && decodeURIComponent(item.dataset["type"]) in LiteGraph.registered_node_types) {
                                    item.dataset["fuzzy"] = "true";
                                    let type = decodeURIComponent(item.dataset["type"])
                                    let newDom = document.createElement("span");
                                    let recordPos = []
                                    if (fuzzy_match_filter(searchWord, type.toLowerCase(), recordPos)) {
                                        let oldDom = item.firstChild.nextSibling;
                                        let oldText = oldDom.textContent;
                                        let newText = highlight_keywords(oldText, recordPos);
                                        oldDom.innerHTML = newText;
                                    } else {
                                        recordPos = []
                                        let node = LiteGraph.registered_node_types[type];
                                        if (node.title && fuzzy_match_filter(searchWord, node.title.toLowerCase(), recordPos)) {
                                            let oldDom = item.firstChild;
                                            let oldText = oldDom.textContent;
                                            let newText = highlight_keywords(oldText, recordPos);
                                            newDom.innerHTML = newText;
                                            item.replaceChild(newDom, oldDom);
                                        }
                                    }
                                }
                            }
                        }
                    });
                    observer.observe(helper, observConfig);
                    let oldClose = helper.parentNode.close;
                    helper.parentNode.close = function () {
                        observer.disconnect();
                        oldClose?.apply(this, arguments)
                    };
                }

				return filtered;
			};
			return dialog;
		}
    }
})