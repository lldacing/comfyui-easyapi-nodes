import {app} from "/scripts/app.js";
import {$el} from "/scripts/ui.js";
import {ComfyWidgets} from "/scripts/widgets.js";

function get_position_style(ctx, node_width, node_height, y, widget_height, isSingle) {
    /* Create a transform that deals with all the scrolling and zooming */
    const elRect = ctx.canvas.getBoundingClientRect();
    if (isSingle) {
        y = y - 86
        y = y + Math.floor((node_height - y - widget_height) / 2)
    }
    const transform = new DOMMatrix()
        .scaleSelf(
            elRect.width / ctx.canvas.width,
            elRect.height / ctx.canvas.height
        )
        .multiplySelf(ctx.getTransform())
        .translateSelf(Math.floor((node_width - widget_height) / 2), y);

    return {
        transformOrigin: '0 0',
        transform: transform,
        left: '0',
        top: '0',
        cursor: 'pointer',
        position: 'absolute',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-around',
        zIndex: '0'
    };
}

function createColorWidget(node, inputName, inputData, app, isSingle) {
    // console.log(node)
    const widget = {
        type: inputData[0], // the type, CHEESE
        name: inputName, // the name, slice
        size: [64, 64], // a default size
        draw(ctx, node, widget_width, y, H) {
            // console.log(node.size[0], node.size[1], y, widget_width, H)
            Object.assign(
                this.div.style,
                get_position_style(ctx, widget_width, node.size[1], y, this.div.clientHeight ? this.div.clientHeight : 0, isSingle)
            );
        },
        computeSize(widget_width) {
            // console.log(widget_width)
            return [64, 64] // a method to compute the current size of the widget
        },
        async serializeValue(nodeId, widgetIndex) {
            let hexa = widget.value || '#000000'
            return hexa
        }
    }
    // adds it to the node
    node.addCustomWidget(widget)
    widget.div = $el('div', {})
    let inputColor = document.createElement('div')
    inputColor.id = 'easyapi-color-picker'
    widget.div.appendChild(inputColor);
    document.body.appendChild(widget.div)
    const picker = Pickr.create({
        el: inputColor,
        theme: 'classic',
        default: '#000000',
        swatches: [
            'rgba(244, 67, 54, 1)',
            'rgba(233, 30, 99, 0.95)',
            'rgba(156, 39, 176, 0.9)',
            'rgba(103, 58, 183, 0.85)',
            'rgba(63, 81, 181, 0.8)',
            'rgba(33, 150, 243, 0.75)',
            'rgba(3, 169, 244, 0.7)',
            'rgba(0, 188, 212, 0.7)',
            'rgba(0, 150, 136, 0.75)',
            'rgba(76, 175, 80, 0.8)',
            'rgba(139, 195, 74, 0.85)',
            'rgba(205, 220, 57, 0.9)',
            'rgba(255, 235, 59, 0.95)',
            'rgba(255, 193, 7, 1)'
        ],
        components: {
            // Main components
            preview: true,
            opacity: true,
            hue: true,
            // Input / output Options
            interaction: {
                hex: true,
                rgba: true,
                hsla: true,
                hsva: true,
                cmyk: true,
                input: true,
                clear: false,
                save: true,
                cancel: true
            }
        }
    })

    picker.on('init', instance => {
        if (!!widget.value) {
            instance.setColor(widget.value);
        }
    }).on('save', (color, instance) => {
        try {
            widget.value = color.toHEXA().toString()
            picker && picker.hide()
        } catch (error) {
        }
    }).on('cancel', instance => {
        picker && picker.hide()
    })

    if (node.picker === undefined) {
        node.picker = [picker]
    } else {
        node.picker.push(picker);
    }
    const handleMouseWheel = () => {
        try {
            if (!!node.picker) {
                for (let idx in node.picker) {
                    node.picker[idx].hide()
                }
            }
        } catch (error) {
        }
    }
    // close selector
    document.addEventListener('wheel', handleMouseWheel)

    const onRemoved = node.onRemoved
    node.onRemoved = () => {
        try {
            for (let idx in node.picker) {
                if (!!node.picker[idx].widgets) {
                    for (let wIdx in node.picker[idx].widgets) {
                        node.picker[idx].widgets[wIdx].div && node.picker[idx].widgets[wIdx].div.remove()
                    }
                }
                node.picker[idx].destroyAndRemove();
            }
            node.picker = null
            document.removeEventListener('wheel', handleMouseWheel)
        } catch (error) {
            console.log(error)
        }
        return onRemoved?.()
    }
    node.serialize_widgets = true
    return widget;
}

app.registerExtension({
    name: "Comfy.EasyApi.custom",
    async init(app) {
        // Any initial setup to run as soon as the page loads
        $el('link', {
            rel: 'stylesheet',
            href: '/extensions/comfyui-easyapi-nodes/css/classic.min.css',
            parent: document.head
        })
    },
    async setup(app) {

    },
    async addCustomNodeDefs(defs, app) {
        // Add custom node definitions
        // These definitions will be configured and registered automatically
        // defs is a lookup core nodes, add yours into this
    },
    async getCustomWidgets(app) {
        // Return custom widget types
        // See ComfyWidgets for widget examples
        return {
            SINGLECOLORPICKER(node, inputName, inputData, app) {
                return createColorWidget(node, inputName, inputData, app, true)
            },
            COLORPICKER(node, inputName, inputData, app) {
                return createColorWidget(node, inputName, inputData, app, false)
            }
        }
    },

    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        // Allows the extension to add additional handling to the node before it is registered with LGraph
        const onDrawForeground = nodeType.prototype.onDrawForeground;
        nodeType.prototype.onDrawForeground = function (ctx) {
            const r = onDrawForeground?.apply?.(this, arguments);
            if (this.flags.collapsed) {
                if (this.picker && this.widgets) {
                    for (const i in this.widgets) {
                        let w = this.widgets[i]
                        if (w.type == 'SINGLECOLORPICKER' || w.type == 'COLORPICKER') {
                            // hide it
                            w.div.style = "";
                        }
                    }
                }
            }

            return r;
        };

        if (nodeData.name === "ShowString" || nodeData.name === "ShowInt" || nodeData.name === "ShowNumber" || nodeData.name === "ShowFloat" || nodeData.name === "ShowBoolean") {
            const outSet = function (text) {
				if (this.widgets) {
                    // if multiline is true, w.type will be customtext
                    // find the position of first "customtext"
					const pos = this.widgets.findIndex((w) => w.type === "customtext");
					if (pos !== -1) {
						for (let i = pos; i < this.widgets.length; i++) {
							this.widgets[i].onRemove?.();
						}
						this.widgets.length = pos;
					}
				}

                if (Array.isArray(text)) {
                    for (const list of text) {
                        const w = ComfyWidgets.STRING(this, "text", ["STRING", {multiline: true}], app).widget;
                        w.inputEl.readOnly = true;
                        w.inputEl.style.opacity = "0.6";
                        w.value = list;
                    }
                } else {
                    const w = ComfyWidgets.STRING(this, "text", ["STRING", {multiline: true}], app).widget;
                    w.inputEl.readOnly = true;
                    w.inputEl.style.opacity = "0.6";
                    w.value = text;
                }

				requestAnimationFrame(() => {
					const sz = this.computeSize();
					if (sz[0] < this.size[0]) {
						sz[0] = this.size[0];
					}
					if (sz[1] < this.size[1]) {
						sz[1] = this.size[1];
					}
					this.onResize?.(sz);
					app.graph.setDirtyCanvas(true, false);
				});
			}

            const onExecuted = nodeType.prototype.onExecuted;
            nodeType.prototype.onExecuted = function (texts) {
                onExecuted?.apply(this, arguments);
                let show = []
                for (let k in texts) {
                    show.push(texts[k])
                }
                outSet.call(this, show);
            };
            /*const onConfigure = nodeType.prototype.onConfigure;
            nodeType.prototype.onConfigure = function (w) {
                onConfigure?.apply(this, arguments);
                if (w?.widgets_values?.length) {
                    outSet.call(this, w.widgets_values[0]);
                }
            };*/
        }
    },
    async registerCustomNodes(app) {
        // Register any custom node implementations here allowing for more flexability than a custom node def
        // console.log("[logging]", "register custom nodes");
    },
    async loadedGraphNode(node, app) {
        // Fires for each node when loading/dragging/etc a workflow json or png
        // If you break something in the backend and want to patch workflows in the frontend
        // This fires for every node on each load so only log once
        // delete ext.loadedGraphNode;

    },
    async nodeCreated(node, app) {
        // Fires every time a node is constructed
        // You can modify widgets/add handlers/etc here
    }
})