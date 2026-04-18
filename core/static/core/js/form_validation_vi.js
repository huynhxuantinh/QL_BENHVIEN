(() => {
    const STYLE_ID = "form-validation-vi-style";
    const BANNER_CLASS = "form-client-error";

    if (!document.getElementById(STYLE_ID)) {
        const style = document.createElement("style");
        style.id = STYLE_ID;
        style.textContent = `
            .${BANNER_CLASS}{
                margin:0 0 12px;
                padding:10px 12px;
                border-radius:10px;
                border:1px solid rgba(180,52,52,.35);
                background:rgba(248,225,225,.75);
                color:#7f2f2f;
                font-size:14px;
                line-height:1.45;
            }
        `;
        document.head.appendChild(style);
    }

    function getMessage(field) {
        const validity = field.validity;
        const tag = (field.tagName || "").toLowerCase();
        const type = (field.getAttribute("type") || "").toLowerCase();
        const title = (field.getAttribute("title") || "").trim();
        const labelText = (field.getAttribute("aria-label") || "").trim();
        const name = labelText || field.getAttribute("placeholder") || field.name || "trường này";

        if (validity.valueMissing) {
            if (tag === "select") {
                return "Vui lòng chọn thông tin bắt buộc.";
            }
            return "Vui lòng nhập thông tin bắt buộc.";
        }
        if (validity.typeMismatch) {
            if (type === "email") {
                return "Vui lòng nhập địa chỉ email hợp lệ.";
            }
            if (type === "url") {
                return "Vui lòng nhập đường dẫn hợp lệ.";
            }
            return "Dữ liệu chưa đúng định dạng.";
        }
        if (validity.patternMismatch) {
            if (title) {
                return title;
            }
            return `Dữ liệu ở ${name} chưa đúng định dạng.`;
        }
        if (validity.tooShort) {
            return `Vui lòng nhập ít nhất ${field.minLength} ký tự.`;
        }
        if (validity.tooLong) {
            return `Vui lòng nhập tối đa ${field.maxLength} ký tự.`;
        }
        if (validity.rangeUnderflow) {
            return `Giá trị phải lớn hơn hoặc bằng ${field.min}.`;
        }
        if (validity.rangeOverflow) {
            return `Giá trị phải nhỏ hơn hoặc bằng ${field.max}.`;
        }
        if (validity.stepMismatch) {
            return "Giá trị nhập vào chưa đúng bước hợp lệ.";
        }
        if (validity.badInput) {
            return "Giá trị nhập vào không hợp lệ.";
        }
        return "Vui lòng kiểm tra lại thông tin đã nhập.";
    }

    function ensureBanner(form) {
        let banner = form.querySelector(`.${BANNER_CLASS}`);
        if (!banner) {
            banner = document.createElement("div");
            banner.className = BANNER_CLASS;
            banner.hidden = true;
            form.insertBefore(banner, form.firstChild);
        }
        return banner;
    }

    function setBanner(form, message) {
        const banner = ensureBanner(form);
        if (!message) {
            banner.hidden = true;
            banner.textContent = "";
            return;
        }
        banner.hidden = false;
        banner.textContent = message;
    }

    function updateCustomValidity(field) {
        if (!field || typeof field.checkValidity !== "function") {
            return "";
        }
        field.setCustomValidity("");
        if (field.checkValidity()) {
            return "";
        }
        const message = getMessage(field);
        field.setCustomValidity(message);
        return message;
    }

    function bindFormValidation(form) {
        form.addEventListener(
            "invalid",
            (event) => {
                const field = event.target;
                const message = updateCustomValidity(field);
                if (message) {
                    setBanner(form, message);
                }
            },
            true
        );

        form.addEventListener("submit", (event) => {
            const fields = form.querySelectorAll("input, select, textarea");
            let firstInvalid = null;

            fields.forEach((field) => {
                const message = updateCustomValidity(field);
                if (!firstInvalid && message) {
                    firstInvalid = field;
                }
            });

            if (firstInvalid) {
                event.preventDefault();
                const message = firstInvalid.validationMessage || getMessage(firstInvalid);
                setBanner(form, message);
                firstInvalid.reportValidity();
                firstInvalid.focus({ preventScroll: true });
                firstInvalid.scrollIntoView({ behavior: "smooth", block: "center" });
            }
        });

        const clearError = (event) => {
            const field = event.target;
            if (!field || typeof field.setCustomValidity !== "function") {
                return;
            }
            field.setCustomValidity("");
            if (field.checkValidity()) {
                setBanner(form, "");
            }
        };

        form.addEventListener("input", clearError, true);
        form.addEventListener("change", clearError, true);
    }

    document.querySelectorAll("form").forEach(bindFormValidation);
})();
