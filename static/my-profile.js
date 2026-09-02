document.addEventListener("DOMContentLoaded", function () {

    const editBtn = document.getElementById("editBtn");
    const cancelBtn = document.getElementById("cancelBtn");

    const viewMode = document.getElementById("viewMode");
    const editMode = document.getElementById("editMode");

    const profileForm = document.getElementById("profileForm");

    const nameInput = document.getElementById("name");
    const phoneInput = document.getElementById("phone");
    const addressInput = document.getElementById("address");

    const nameError = document.getElementById("nameError");
    const phoneError = document.getElementById("phoneError");
    const addressError = document.getElementById("addressError");

    const profilePictureInput =
        document.getElementById("profilePictureInput");

    const editPreview =
        document.getElementById("editPreview");

    const editPlaceholder =
        document.getElementById("editPlaceholder");


    /* =========================
       SHOW EDIT MODE
    ========================= */

    editBtn.addEventListener("click", function () {

        viewMode.style.display = "none";
        editMode.classList.add("active");
        editBtn.style.display = "none";

    });


    /* =========================
       CANCEL EDIT
    ========================= */

    cancelBtn.addEventListener("click", function () {

        editMode.classList.remove("active");
        viewMode.style.display = "grid";
        editBtn.style.display = "inline-flex";

        clearAllErrors();

        if (profilePictureInput) {
            profilePictureInput.value = "";
        }

    });


    /* =========================
       ERROR FUNCTIONS
    ========================= */

    function showError(element, message) {

        element.textContent = message;
        element.style.display = "block";

    }


    function clearError(element) {

        element.textContent = "";
        element.style.display = "none";

    }


    function clearAllErrors() {

        clearError(nameError);
        clearError(phoneError);
        clearError(addressError);

    }


    /* =========================
       NAME VALIDATION
    ========================= */

    function validateName() {

        const value = nameInput.value.trim();

        const namePattern =
            /^[A-Za-z][A-Za-z\s.'-]{1,49}$/;


        if (value === "") {

            showError(
                nameError,
                "Name is required."
            );

            return false;
        }


        if (value.length < 2) {

            showError(
                nameError,
                "Name must be at least 2 characters."
            );

            return false;
        }


        if (value.length > 50) {

            showError(
                nameError,
                "Name must be 50 characters or less."
            );

            return false;
        }


        if (!namePattern.test(value)) {

            showError(
                nameError,
                "Please enter a valid name."
            );

            return false;
        }


        clearError(nameError);

        return true;
    }


    /* =========================
       PHONE VALIDATION
    ========================= */

    function validatePhone() {

        const value = phoneInput.value.trim();


        if (value === "") {

            showError(
                phoneError,
                "Phone number is required."
            );

            return false;
        }


        if (value.length < 10) {

            showError(
                phoneError,
                "10 digits are required."
            );

            return false;
        }


        if (value.length > 10) {

            showError(
                phoneError,
                "Phone number must contain 10 digits."
            );

            return false;
        }


        if (!/^[6-9]/.test(value)) {

            showError(
                phoneError,
                "Mobile number must start with 6, 7, 8 or 9."
            );

            return false;
        }


        clearError(phoneError);

        return true;
    }


    /* =========================
       ADDRESS VALIDATION
    ========================= */

    function validateAddress() {

        const value = addressInput.value.trim();


        if (value === "") {

            showError(
                addressError,
                "Address is required."
            );

            return false;
        }


        if (value.length < 5) {

            showError(
                addressError,
                "Address must be at least 5 characters."
            );

            return false;
        }


        if (value.length > 200) {

            showError(
                addressError,
                "Address must be 200 characters or less."
            );

            return false;
        }


        clearError(addressError);

        return true;
    }


    /* =========================
       LIVE NAME VALIDATION
    ========================= */

    nameInput.addEventListener("input", function () {

        validateName();

    });


    /* =========================
       PHONE INPUT
       ONLY NUMBERS ALLOWED
    ========================= */

    phoneInput.addEventListener("input", function () {

        /* Remove anything that is not a number */

        this.value = this.value.replace(/\D/g, "");


        /* Maximum 10 digits */

        if (this.value.length > 10) {

            this.value = this.value.substring(0, 10);

        }


        validatePhone();

    });


    /* =========================
       ADDRESS LIVE VALIDATION
    ========================= */

    addressInput.addEventListener("input", function () {

        validateAddress();

    });


    /* =========================
       PROFILE PICTURE
    ========================= */

    profilePictureInput.addEventListener(
        "change",
        function () {

            const file = this.files[0];

            if (!file) {
                return;
            }


            const allowedTypes = [
                "image/png",
                "image/jpeg",
                "image/webp"
            ];


            if (!allowedTypes.includes(file.type)) {

                alert(
                    "Please select a PNG, JPG or WEBP image."
                );

                this.value = "";

                return;
            }


            if (file.size > 5 * 1024 * 1024) {

                alert(
                    "Profile picture must be smaller than 5 MB."
                );

                this.value = "";

                return;
            }


            const reader = new FileReader();


            reader.onload = function (event) {

                if (editPreview) {

                    editPreview.src =
                        event.target.result;

                    editPreview.style.display =
                        "block";
                }


                if (editPlaceholder) {

                    editPlaceholder.style.display =
                        "none";
                }

            };


            reader.readAsDataURL(file);

        }
    );


    /* =========================
       SAVE CHANGES
    ========================= */

    profileForm.addEventListener(
        "submit",
        function (event) {

            event.preventDefault();


            const nameValid = validateName();
            const phoneValid = validatePhone();
            const addressValid = validateAddress();


            /* Stop if anything is wrong */

            if (
                !nameValid ||
                !phoneValid ||
                !addressValid
            ) {

                return;

            }


            /* Clean spaces before submitting */

            nameInput.value =
                nameInput.value.trim();

            phoneInput.value =
                phoneInput.value.trim();

            addressInput.value =
                addressInput.value.trim();


            /* Everything is valid */

            this.submit();

        }
    );

});