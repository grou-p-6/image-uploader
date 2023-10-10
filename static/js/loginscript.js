const validate = (username, password) => {
	if (username == "" || password == "") {
		alert("Please enter username and password");
		return false;
	}

	if (password.length < 8) {
		alert("Password must be at least 8 characters");
		return false;
	}

	if (username.length > 20) {
		alert("Username must be less than 20 characters");
		return false;
	}

	return true;
};

const login = () => {
	username = document.getElementById("username").value;
	password = document.getElementById("password").value;

	console.log("Starting login");
	document.getElementById("loaderModal").style.display = "block";

	if (!validate(username, password)) {
		document.getElementById("loaderModal").style.display = "none";
		return;
	}

	fetch("/login", {
		method: "POST",
		body: JSON.stringify({
			username: username,
			password: password,
		}),
		headers: {
			"Content-type": "application/json; charset=UTF-8",
		},
	})
		.then(async (response) => {
			const data = await response.json();
			console.log(data.message);
			if (response.status == 400) {
				alert(data.message);
				document.getElementById("loaderModal").style.display = "none";
			} else {
				window.location.href = "/";
			}
		})
		.catch((error) => {
			console.error("Error:", error);
			document.getElementById("loaderModal").style.display = "none";
		});
};

const signup = () => {
	username = document.getElementById("username").value;
	password = document.getElementById("password").value;

	console.log("Starting signup");
	document.getElementById("loaderModal").style.display = "block";

	if (!validate(username, password)) {
		document.getElementById("loaderModal").style.display = "none";
		return;
	}

	fetch("/api/signup", {
		method: "POST",
		body: JSON.stringify({
			username: username,
			password: password,
		}),
		headers: {
			"Content-type": "application/json; charset=UTF-8",
		},
	})
		.then(async (response) => {
			const data = await response.json();
			console.log(data.message);
			if (response.status == 400) {
				alert(data.message);
				document.getElementById("loaderModal").style.display = "none";
			} else {
				window.location.href = "/";
			}
		})
		.catch((error) => {
			console.error("Error:", error);
			document.getElementById("loaderModal").style.display = "none";
		});
};
