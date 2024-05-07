import { app } from "/scripts/app.js";
import { $el } from "/scripts/ui.js";
import { GroupNodeHandler } from '/extensions/core/groupNode.js'
import { EasyApiDialog } from './dialog.js'

const style = `
#comfy-save-button, #comfy-dev-save-api-button {
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
.easyapi-dialog {
    padding-top: 40px;
}
.easyapi-node-set {
	width: 500px;
}
.easyapi-node-set button {
	font-size: 100%;
}
.easyapi-node-set table, easyapi-node-set-all table {
	width: 100%;
}
.easyapi-node-set td, .easyapi-node-set-all td {
    border: 1px solid white;
    padding: 2px 4px;
}
`;

class EasyApiWorkflows {

	constructor() {
		this.nodeSetDialog = new EasyApiDialog();
	}
	registerSettingMenu() {
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
				} else if (node.class_type == "LoadImageMask") {
					output[o].class_type = "Base64ToMask";
					output[o].inputs = {
						"base64Images":"",
						"channel": "red"
					}
				}
				delete output[o]['_meta']
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

		function showTip(tips) {
			app.ui.dialog.show(tips);
			setTimeout(() => app.ui.dialog.close(), 500);
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
					title: "Copy Api",
					callback: async () => {
						app.graphToPrompt().then(p => {
							const apiObj = p.output;
							const json = JSON.stringify(apiObj, null, null);
							copyToClipboard(json);
							showTip("Copied")
						});
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
							showTip("Copied")
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
							const json = JSON.stringify(p.workflow, null, null); // convert the data to a JSON string
							copyToClipboard(json);
							showTip("Copied")
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
	registerContextMenu() {
		const that = this;
		/*const ctxMenu = LiteGraph.ContextMenu;
		LiteGraph.ContextMenu = function (values, options) {
			options = options || {};
			options.autoopen = true;
			const ctx = ctxMenu.call(this, values, options);
			return ctx;
		}
		LiteGraph.ContextMenu.prototype = ctxMenu.prototype;*/


		const orig = LGraphCanvas.prototype.getCanvasMenuOptions;

		function showNodeIdSettingDialog(menu, nodes) {
			that.nodeSetDialog.title("Set Node Id: " + menu.content)
				.resetPos()
				.show($el(
					"div.easyapi-node-set-all",
					{
						style: {
							color: "white"
						}
					},
					[
						$el(
							"div.easyapi-node-set-all-target",
							{},
							[
								$el("table",
									{
										style: {
											borderCollapse: "collapse"
										},
										$: (element) => {
											nodes.forEach((n, index) => {
												let line =
													$el("tr",
														{},
														[
															$el("td",
																{},
																[
																	$el(
																		"div",
																		{},
																		[
																			$el(
																				"button",
																				{
																					textContent: "Locate",
																					style: {
																						width: "80px",
																					},
																					onclick: () => {
																						app.canvas.centerOnNode(n);
																						app.canvas.selectNode(n, false);
																					}
																				}
																			)
																		]
																	)
																]
															),
															that.createTd(n.id),
															that.createTd(index + 1, {style:{color: "red"}}),
															that.createTd(n.type),
															that.createTd(n.title),
															that.createTd(!!n.isVirtualNode ? "√" : ""),
														]
													);
												element.append(line);
											});
										}
									},
									[
										$el("tr",
											{},
											[
												$el("th",
													{
														textContent: "Node Info",
														colSpan: 5,
													}
												)
											]
										),
										$el("tr",
											{
												style: {
													textAlign: "center"
												}
											},
											[
												that.createTd("Action"),
												that.createTd("Node Id"),
												that.createTd("New Node Id"),
												that.createTd("Node Type"),
												that.createTd("Node Title"),
												that.createTd("Is Virtual"),
											]
										),
									]
								),
							]
						),
					]
				), true, (dialog) => {
					// console.log(nodes)
					that.updateAllNodeId(nodes);
					// console.log(nodes)
					dialog.close();
				});
		}

		LGraphCanvas.prototype.getCanvasMenuOptions = function () {
			const options = orig.apply(this, arguments);
			that.nodeSetDialog.close();
			if (options.length >= 1 && options[options.length - 1] !== null) {
				// add separator
				options.push(null);
			}
			const virtualNodeInTail = (a, b) => {
				if (a.isVirtualNode && !b.isVirtualNode) {
					return 1;
				} else if (!a.isVirtualNode && b.isVirtualNode) {
					return -1;
				}
				return 0;
			};
			const virtualNodeInHead = (a, b) => {
				if (a.isVirtualNode && !b.isVirtualNode) {
					return -1;
				} else if (!a.isVirtualNode && b.isVirtualNode) {
					return 1;
				}
				return 0;
			};
			const min_x_y = (a, b) => {
				// left to right
				let diff = a.pos[0] - b.pos[0]
				let offsetValue = 30
				if (Math.abs(diff) < offsetValue) {
					return a.pos[1] - b.pos[1]
				}
				return diff;
			};
			const min_y_x = (a, b) => {
				// top to bottom
				let diff = a.pos[1] - b.pos[1]
				let offsetValue = 30
				if (Math.abs(diff) < offsetValue) {
					return a.pos[0] - b.pos[0]
				}
				return diff;
			};
			options.push({
				content: "Reset All Node Id (EasyApi)",
				has_submenu: true,
				submenu: {
					options: [{
						content: "Order L -> R",
						has_submenu: false,
						callback: (item, options, e, menu, extra) => {
							const nodes = app.graph._nodes;
							let sortArray = [min_x_y]
							sortArray.forEach(sortFn => nodes.sort(sortFn));
							showNodeIdSettingDialog(item, nodes);
						},
					},
					{
						content: "Order L -> R and virtual node at the tail",
						has_submenu: false,
						callback: (item, options, e, menu, extra) => {
							const nodes = app.graph._nodes;
							let sortArray = [min_x_y, virtualNodeInTail]
							sortArray.forEach(sortFn => nodes.sort(sortFn));
							showNodeIdSettingDialog(item, nodes);
						},
					},
					{
						content: "Order L -> R and virtual node at the head",
						has_submenu: false,
						callback: (item, options, e, menu, extra) => {
							const nodes = app.graph._nodes;
							let sortArray = [min_x_y, virtualNodeInHead]
							sortArray.forEach(sortFn => nodes.sort(sortFn));
							showNodeIdSettingDialog(item, nodes);
						},
					},
					{
						content: "Order T -> B",
						has_submenu: false,
						callback: (item, options, e, menu, extra) => {
							const nodes = app.graph._nodes;
							let sortArray = [min_y_x]
							sortArray.forEach(sortFn => nodes.sort(sortFn));
							showNodeIdSettingDialog(item, nodes);
						},
					},
					{
						content: "Order T -> B and virtual node at the tail",
						has_submenu: false,
						callback: (item, options, e, menu, extra) => {
							const nodes = app.graph._nodes;
							let sortArray = [min_y_x, virtualNodeInTail]
							sortArray.forEach(sortFn => nodes.sort(sortFn));
							showNodeIdSettingDialog(item, nodes);
						},
					},
					{
						content: "Order T -> B and virtual node at the head",
						has_submenu: false,
						callback: (item, options, e, menu, extra) => {
							const nodes = app.graph._nodes;
							let sortArray = [min_y_x, virtualNodeInHead]
							sortArray.forEach(sortFn => nodes.sort(sortFn));
							showNodeIdSettingDialog(item, nodes);
						},
					},]
				}
			});

			return options;
		};
	}
	registerNodeContextMenu() {
		const that = this;
		/**
		 * 找到目标节点id对应的所有节点，并在指定table中显示
		 * @param tableElement
		 * @param nodes
		 * @param originNode
		 * @param targetId
		 */
		function listByNodeId(tableElement, nodes, originNode, targetId) {
			let filterNodes = nodes.filter(n => n.id == targetId).map(n => {
				let line =
					$el("tr",
						{},
						[
							that.createTd(n.id == originNode.id ? '[Self] ' + n.type : n.type),
							$el("td",
								{},
								[
									$el(
										"div",
										{},
										[
											$el(
												"span",
												{
													textContent: n.title
												}
											),
											$el(
												"button",
												{
													textContent: "Locate",
													style: {
														width: "60px",
														cssFloat: "right"
													},
													onclick: () => {
														app.canvas.centerOnNode(n);
														app.canvas.selectNode(n, false);
													}
												}
											)
										]
									)
								]
							)
						]
					)
				return line
			});
			if (filterNodes.length > 0) {
				tableElement.append($el("tr",
					{},
					[
						$el("th",
							{
								textContent: "Nodes found with new id",
								colSpan: 2,
							}
						)
					]
				));
				tableElement.append(...filterNodes)
			}
		}
		const getNodeMenuOptions = LGraphCanvas.prototype.getNodeMenuOptions;
		LGraphCanvas.prototype.getNodeMenuOptions = function (node) {
			const options = getNodeMenuOptions.apply(this, arguments);
			that.nodeSetDialog.close();
			if (!GroupNodeHandler.isGroupNode(node)) {
				const nodes = node.graph._nodes;
				nodes.sort((a, b) => {
					if (a.isVirtualNode && !b.isVirtualNode) {
						return 1;
					} else if (!a.isVirtualNode && b.isVirtualNode) {
						return -1;
					}
					return a.pos[0] - b.pos[0] + a.pos[1] - b.pos[1];
				});
				if (options.length >= 2 && options[options.length - 2] !== null) {
					// last menu is remove
					// add separator
					options.splice(options.length - 1, 0, null);
				}
				let hasInputLink = node.inputs?.filter(input => input?.link).length > 0;
				let hasOutputLink = node.outputs?.filter(output => output?.links?.length > 0).length > 0;
				options.splice(options.length - 1, 0,
					{
						content: "Set Node Id (EasyApi)",
						callback: (item, options, e, menu, node) => {
							that.nodeSetDialog.title(item.content).resetPos().show($el(
								"div.easyapi-node-set",
								{
									style: {
										color: "white"
									}
								},
								[
									$el(
										"div.easyapi-node-set-target",
										{},
										[
											$el("table",
												{
													style: {
														borderCollapse: "collapse"
													},
												},
												[
													$el("tr",
														{},
														[
															$el("th",
																{
																	textContent: "Node Info",
																	colSpan: 2,
																}
															)
														]
													),
													$el("tr",
														{},
														[
															that.createTd("Node Id"),
															$el("td",
																{},
																[
																	$el(
																		"div",
																		{},
																		[
																			$el(
																				"span",
																				{
																					textContent: node.id
																				}
																			),
																			$el(
																				"button",
																				{
																					textContent: "Locate",
																					style: {
																						width: "60px",
																						cssFloat: "right"
																					},
																					onclick: () => {
																						app.canvas.centerOnNode(node);
																						app.canvas.selectNode(node, false);
																					}
																				}
																			)
																		]
																	)
																]
															)
														]
													),
													$el("tr",
														{},
														[
															that.createTd("Node Type"),
															that.createTd(node.type)
														]
													),
													$el("tr",
														{},
														[
															that.createTd("Node Title"),
															that.createTd(node.title)
														]
													),
													$el("tr",
														{},
														[
															that.createTd("New Node Id"),
															$el("td",
																{},
																[
																	$el(
																		"input",
																		{
																			id: "easyapi-node-new-id",
																			type: "number",
																			value: node.id,
																			min: 1,
																			step: 1,
																			style: {
																				paddingLeft: "6px",
																			},
																			onkeypress: (e) => {
																				let keyCode = e.keyCode;
																				if (!(keyCode >= 48 && keyCode <= 57)) {
																					e.preventDefault();
																				}
																			},
																			oninput: (e) => {
																				let el = e.target;
																				if (el.value) {
																					el.value = el.value.replace(/[^\d]/g, '');
																				} else {
																					el.value = node.id
																				}
																				let repeatNodesTable = document.getElementById("easyapi-repeat-id-nodes")
																				repeatNodesTable.innerHTML = ""
																				listByNodeId(repeatNodesTable, nodes, node, el.value)
																				if (!node.graph._nodes_by_id[el.value]) {
																					that.nodeSetDialog.showSaveBtn();
																				} else {
																					that.nodeSetDialog.hideSaveBtn();
																				}
																			},
																		}
																	)
																]
															)
														]
													)
												]
											),
											$el("table",
												{
													id: "easyapi-repeat-id-nodes",
													style: {
														borderCollapse: "collapse"
													},
													$: (element) => listByNodeId(element, nodes, node, node.id)
												},
												[]
											),
										]
									),
								]
							), false, (dialog) => {
								let inputNodeId = document.getElementById("easyapi-node-new-id")
								// console.log(nodes)
								// console.log(node.graph._nodes_by_id)
								let newNodeId = parseInt(inputNodeId.value);
								let oldNodeId = node.id
								if (newNodeId != oldNodeId) {
									that.setNewIdForNode(node, newNodeId)
									node.setDirtyCanvas(true, true);
								}
								// console.log(nodes)
								// console.log(node.graph._nodes_by_id)
								dialog.close()
							});
						}
					},
					{
						content: "Go To Link Node (EasyApi)",
						disabled: !hasInputLink && !hasOutputLink,
						has_submenu: hasInputLink || hasOutputLink,
						submenu: {
							options: [
								{
									content: "Input",
									disabled: !hasInputLink,
									has_submenu: hasInputLink,
									submenu: {
										options: node.inputs?.filter(input => input?.link)
											.map((input) => {
												let linkId = input.link;
												let llink = node.graph.links[linkId];
												let inputNodeId = llink.origin_id;
												let inputNode = node.graph._nodes_by_id[inputNodeId]
												return {
													content: `${input.name} - ${input.type}`,
													has_submenu: true,
													submenu: {
														options: [{
															content: `${inputNode.getOutputInfo(llink.origin_slot)?.name} - ${inputNode.getTitle()} - #${inputNode.id} (${inputNode.pos[0]}, ${inputNode.pos[1]})`,
															callback: (item, options, e, menu, extra) => {
																app.canvas.centerOnNode(inputNode);
																app.canvas.selectNode(inputNode, false);
															}
														}]
													}
												}
											})
									}
								},
								{
									content: "Output",
									disabled: !hasOutputLink,
									has_submenu: hasOutputLink,
									submenu: {
										options: node.outputs?.filter(output => output?.links?.length > 0)
											.map((output) => {
												return {
													content: `${output.name} - ${output.type}`,
													has_submenu: true,
													submenu: {
														options: output.links.map((linkId) => {
															let llink = node.graph.links[linkId];
															let outputNodeId = llink.target_id;
															let outputNode = node.graph._nodes_by_id[outputNodeId];
															return {
																content: `${outputNode.getInputInfo(llink.target_slot)?.name} - ${outputNode.getTitle()} - #${outputNode.id} (${outputNode.pos[0]}, ${outputNode.pos[1]})`,
																callback: (item, options, e, menu, extra) => {
																	app.canvas.centerOnNode(outputNode);
																	app.canvas.selectNode(outputNode, false);
																}
															};
														})
													}
												}
											})
									}
								}
							]
						}
					},
					null
				);
			}
			return options;
		};
	}

	createTd(content, options) {
		return $el("td",
			Object.assign({
				textContent: content,
			}, options || {})
		);
	}

	setNewIdForNode(node, newNodeId) {

		let oldNodeId = node.id;
		node.id = newNodeId;
		if (node.id != oldNodeId) {
			// update node id
			node.graph._nodes_by_id[node.id] = node
			delete node.graph._nodes_by_id[oldNodeId]
			// update links
			for (let idx in node.graph.links) {
				let lLink = node.graph.links[idx];
				if (lLink.origin_id == oldNodeId) {
					lLink.origin_id = node.id;
				}
				if (lLink.target_id == oldNodeId) {
					lLink.target_id = node.id;
				}
			}
			// update app.nodeOutputs
			if(oldNodeId in app.nodeOutputs) {
				app.nodeOutputs[newNodeId] = app.nodeOutputs[oldNodeId]
				delete app.nodeOutputs[oldNodeId]
			}
			// update app.nodePreviewImages
			if(oldNodeId in app.nodePreviewImages) {
				app.nodePreviewImages[newNodeId] = app.nodePreviewImages[oldNodeId]
				delete app.nodePreviewImages[oldNodeId]
			}
			if (newNodeId > app.graph.last_node_id) {
				app.graph.last_node_id = newNodeId;
			}
		}
	}

	updateAllNodeId(nodes) {
		// find max node id
		const maxId = Math.max(...(nodes.map(n => n.id)));
		// Prepare: set id to unused number
		for (let i = 0; i < nodes.length; i++) {
			let node = nodes[i];
			let newNodeId = maxId + i + 1;
			this.setNewIdForNode(node, newNodeId);
		}
		// Starting from 1, set id
		for (let i = 0; i < nodes.length; i++) {
			let node = nodes[i];
			let newNodeId = i + 1;
			this.setNewIdForNode(node, newNodeId);
		}
		app.graph.last_node_id = nodes.length;
		app.graph.setDirtyCanvas(true, true);
	}
}

app.registerExtension({
	name: "Comfy.EasyApi.Workflows",
	init() {
		$el("style", {
			textContent: style,
			parent: document.head,
		});
	},
	async setup() {
		let workflows = new EasyApiWorkflows();
		workflows.registerSettingMenu();
		workflows.registerContextMenu();
		workflows.registerNodeContextMenu()
	},
});
