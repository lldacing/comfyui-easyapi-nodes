import { app } from "/scripts/app.js";
import { api } from "/scripts/api.js";
// ================= CREATE EXTENSION ================
/*app.registerExtension({
    name: "Comfy.EasyApiImageNode",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "Base64ToImage") {
            console.log(nodeData)
        }
    },
});*/
api.addEventListener("executed", ({detail}) => {
    const images = detail?.output?.base64Images;
    if (!images) return;
    const currentNode = app.graph._nodes_by_id[detail.node];
    // console.log(currentNode.imgs)
    currentNode.imgs = [];
    for(let i in images){
        let img = images[i]
        let image = new Image()
        image.onload = () => {
            currentNode.imgs.push(image);
            currentNode.setSizeForImage?.();
            app.graph.setDirtyCanvas(true, true);
        };
        image.src=img;
    }
});
// ================= END CREATE EXTENSION ================
