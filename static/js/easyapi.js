import { app } from "/scripts/app.js";
import { api } from "/scripts/api.js";
import { debounce } from "./debounce.js"

app.registerExtension({
    name: "Comfy.EasyApi.Setting",
    async setup(app) {
		const res = await api.fetchApi("/easyapi/history/maxSize")
		const jsonData = await res.json() || {};
		const max = jsonData['maxSize'] || 10000
		const changeFun = debounce((n, o) => api.fetchApi("/easyapi/history/size", {
					method: 'POST',
					headers: {
						"content-type": "application/json",
					},
					body: JSON.stringify({
						maxSize: n
					})
				}), 1000, false)
        const setting = app.ui.settings.addSetting({
			id: name,
			name: "Maximum History Size",
			defaultValue: max,
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
})