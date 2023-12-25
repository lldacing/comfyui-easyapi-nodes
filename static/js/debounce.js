/**
 * 防抖函数
 * @param fn
 * @param delay
 * @param immediate
 * @returns {function(...[*]): Promise<unknown>}
 * @source https://juejin.cn/post/7075890311649558541
 */
export function debounce(fn, delay, immediate = false) {
    // 1.定义一个定时器, 保存上一次的定时器
    let timer = null
    let isInvoke = false

    // 2.真正执行的函数
    const _debounce = function (...args) {
        return new Promise((resolve, reject) => {
            // 取消上一次的定时器
            if (timer) clearTimeout(timer)

            // 判断是否需要立即执行
            if (immediate && !isInvoke) {
                const result = fn.apply(this, args)
                resolve(result)
                isInvoke = true
            } else {
                // 延迟执行
                timer = setTimeout(() => {
                    // 外部传入的真正要执行的函数, 拿到函数返回值并调用resolve
                    const result = fn.apply(this, args)
                    resolve(result)
                    isInvoke = false
                    timer = null
                }, delay)
            }
        })
    }

    // 封装取消功能
    _debounce.cancel = function () {
        if (timer) clearTimeout(timer)
        timer = null
        isInvoke = false
    }

    return _debounce
}
