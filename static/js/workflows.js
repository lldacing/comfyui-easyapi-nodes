import { app } from "/scripts/app.js";
import { $el } from "/scripts/ui.js";

const style = `
#comfy-dev-save-api-button {
   position: relative;
   overflow: hidden;
}
.easyapi-workflow-arrow {
   position: absolute;
   top: 0;
   bottom: 0;
   left: 0;
   font-size: 12px;
   display: flex;
   align-items: center;
   width: 24px;
   justify-content: center;
   background: rgba(255,255,255,0.1);
}
.easyapi-workflow-arrow:after {
   content: "▼";
}
.easyapi-workflow-arrow:hover {
   filter: brightness(1.6);
   background-color: var(--comfy-menu-bg);
}
.easyapi-save-popup,.easyapi-dev-save-api-popup {
   border-radius: 6px;
}

`;

class EasyApiWorkflows {

	constructor() {
		function replaceImageNode(apiJsonObj) {
			const output = {};
			for (const o in apiJsonObj) {
				const node = apiJsonObj[o];
				output[o] = node;
				if (node.class_type == "LoadImage" ) {
					output[o].class_type = "Base64ToImage";
					output[o].inputs = {
						"base64Images":""
					}
				} else if (node.class_type == "PreviewImage" || node.class_type == "SaveImage") {
					output[o].class_type = "ImageToBase64";
					output[o].inputs = {
						"images": node.inputs.images
					}
				}
			}
			return output
		}
		function copyToClipboard(text) {
			if (navigator.clipboard) {
				// clipboard api 复制
				navigator.clipboard.writeText(text);
			} else {
				const textarea = document.createElement('textarea');
				document.body.appendChild(textarea);
				// 隐藏此输入框
				textarea.style.position = 'fixed';
				textarea.style.clip = 'rect(0 0 0 0)';
				textarea.style.top = '10px';
				// 赋值
				textarea.value = text;
				// 选中
				textarea.select();
				// 复制
				document.execCommand('copy', true);
				// 移除输入框
				document.body.removeChild(textarea);
			}
		}
		function addWorkflowMenu(type, getOptions) {
			return $el("div.easyapi-workflow-arrow", {
				parent: document.getElementById(`comfy-${type}-button`),
				onclick: (e) => {
					e.preventDefault();
					e.stopPropagation();

					LiteGraph.closeAllContextMenus();
					const menu = new LiteGraph.ContextMenu(
						getOptions(),
						{
							event: e,
							scale: 1.3,
						}
					);
					menu.root.classList.add(`easyapi-${type}-popup`);
				},
			});
		}

		addWorkflowMenu("dev-save-api", () => {
			return [
				{
					title: "Save as",
					callback: () => {
						const orgSaveApiBtn = document.getElementById('comfy-dev-save-api-button');
						orgSaveApiBtn.click();
					},
				},
				{
					title: "Save EasyApi as",
					callback: async () => {
						let filename = "workflow_api(base64).json";
						filename = prompt("Save workflow API (Replace LoadImage to Base64Image, PreviewImage/SaveImage to ImageToBase64) as:", filename);
						if (!filename) return;
						if (!filename.toLowerCase().endsWith(".json")) {
							filename += ".json";
						}

						app.graphToPrompt().then(p => {
							const apiObj = p.output;
							const newApiObj = replaceImageNode(apiObj)
							const json = JSON.stringify(newApiObj, null, null); // convert the data to a JSON string
							const blob = new Blob([json], {type: "application/json"});
							const url = URL.createObjectURL(blob);
							const a = $el("a", {
								href: url,
								download: filename,
								style: {display: "none"},
								parent: document.body,
							});
							a.click();
							setTimeout(function () {
								a.remove();
								window.URL.revokeObjectURL(url);
							}, 0);
						});
					},
				},
				{
					title: "Copy EasyApi",
					callback: async () => {
						app.graphToPrompt().then(p => {
							const apiObj = p.output;
							const newApiObj = replaceImageNode(apiObj)
							const json = JSON.stringify(newApiObj, null, null); // convert the data to a JSON string
							copyToClipboard(json);
							alert("Copied")
						});
					},
				},
			];
		});
		addWorkflowMenu("save", () => {
			return [
				{
					title: "Copy workflow",
					callback: async () => {
						app.graphToPrompt().then(p => {
							const json = JSON.stringify(app.graph.serialize(), null, null); // convert the data to a JSON string
							copyToClipboard(json);
							alert("Copied")
						});
					},
				},
			];
		});

		const handleFile = app.handleFile;
		const self = this;
		app.handleFile = function (file) {
			if (file?.name?.endsWith(".json")) {
				self.workflowName = file.name;
			} else {
				self.workflowName = null;
			}
			return handleFile.apply(this, arguments);
		};
	}
}

let workflows;

app.registerExtension({
	name: "easyapi.Workflows",
	init() {
		$el("style", {
			textContent: style,
			parent: document.head,
		});
	},
	async setup() {
		workflows = new EasyApiWorkflows();
	},
});
