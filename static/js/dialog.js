import { $el, ComfyDialog } from "/scripts/ui.js";

export class EasyApiDialog extends ComfyDialog {
	constructor() {
        super();
        this.element.classList.add("easyapi-dialog");
        this.initTitle();
        this.showSave = false;
        this.saveCb = () => {};
    }

	createButtons() {
        return [
            $el("button.easyapi-dialog-save",
                {
                    type: "button",
                    textContent: "Update",
                    onclick: () => this.save()
                }
            ),
            $el("button", {
                type: "button",
                textContent: "Close",
                onclick: () => this.close(),
            }),
        ];
	}

    title(title) {
        let titleDiv = this.element.querySelector("div.easyapi-dialog-title")
        titleDiv.innerText = title;
        return this;
    }

    resetPos() {
        this.element.style.left="50%";
        this.element.style.top="50%";
        this.element.style.transform="translate(-50%, -50%)";
        return this;
    }
    initTitle() {
        let contentDiv = this.element.querySelector("div.comfy-modal-content")
        let titleDiv = $el("div.easyapi-dialog-title", {
            content: "title",
            style: {
                width: "100%",
                position: "absolute",
                backgroundColor: "#2D2D2D",
                top: 0,
                left: 0,
                textAlign: "center",
                height: "40px",
                lineHeight: "40px",
                cursor: "move",
                color: "#ffffff",
                fontWeight: "bolder",
                borderBottom: "1px solid #161616",
            }
        })
        this.element.insertBefore(titleDiv, contentDiv);
        this.initDragElement(this.element, titleDiv);
    }
    initDragElement(mainEl, titleEl) {
        let offset_x = 0, offset_y = 0, start_x = 0, start_y = 0;
        if (titleEl) {
            /* 如果存在就是移动 DIV 的地方：*/
            titleEl.onmousedown = dragMouseDown;
        } else {
            /* 否则，从 DIV 内的任何位置移动：*/
            mainEl.onmousedown = dragMouseDown;
        }

        function dragMouseDown(e) {
            e = e || window.event;
            e.preventDefault();
            // 在启动时获取鼠标光标位置：
            start_x = e.clientX;
            start_y = e.clientY;
            mainEl.style.opacity="0.9"
            document.onmouseup = closeDragElement;
            // 当光标移动时调用一个函数：
            document.onmousemove = dragMouseMove;
        }

        function dragMouseMove(e) {
            e = e || window.event;
            e.preventDefault();
            // 计算新的光标位置：
            offset_x = start_x - e.clientX;
            offset_y = start_y - e.clientY;
            start_x = e.clientX;
            start_y = e.clientY;
            // 设置元素的新位置：
            mainEl.style.top = (mainEl.offsetTop - offset_y) + "px";
            mainEl.style.left = (mainEl.offsetLeft - offset_x) + "px";
            mainEl.style.width = mainEl.keepWidth + "px";
        }

        function closeDragElement() {
            /* 释放鼠标按钮时停止移动：*/
            mainEl.style.opacity="1"
            document.onmouseup = null;
            document.onmousemove = null;
        }
    }
	close() {
		this.element.style.display = "none";
	}

    save() {
        this.saveCb && this.saveCb(this);
    }
    showSaveBtn(saveBtnLabel="Update") {
        let saveBtn = this.element.getElementsByClassName("easyapi-dialog-save")[0]
        saveBtn.innerHTML = saveBtnLabel;
        saveBtn.style.display = "";
    }
    hideSaveBtn() {
        let saveBtn = this.element.getElementsByClassName("easyapi-dialog-save")[0]
       saveBtn.style.display = "none";
    }

	show(html, showSave, saveCb, saveBtnLabel="Update") {
		if (typeof html === "string") {
			this.textElement.innerHTML = html;
		} else {
			this.textElement.replaceChildren(html);
		}
        this.showSave = showSave || false;
        if (this.showSave) {
            this.showSaveBtn(saveBtnLabel);
        } else {
            this.hideSaveBtn();
        }
        this.saveCb = saveCb
        this.element.style.display = "flex";
        this.element.keepWidth = this.element.clientWidth;
	}
}
