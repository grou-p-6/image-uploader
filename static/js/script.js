function preview() {
	const successLoaderDiv = document.getElementById("uploadSuccess");
	frame.src = URL.createObjectURL(event.target.files[0]);
	successLoaderDiv.style.display = "none";
}

function clearImage() {
	document.getElementById("formFile").value = null;
	frame.src = "";
}

function getImageSize(sizeInBytes) {
	const i = Math.floor(Math.log(sizeInBytes) / Math.log(1024));
	return (
		(sizeInBytes / Math.pow(1024, i)).toFixed(2) * 1 +
		" " +
		["B", "kB", "MB", "GB", "TB"][i]
	);
}

function openModal(imageData) {
	const modalImg = document.getElementById("modalImage");
	modalImg.src = imageData.url;
	const imageModal = new bootstrap.Modal(document.getElementById("imageModal"));
	document.getElementById("imageName").textContent = imageData.image_name
		.split("_")
		.slice(2)
		.join("_");
	document.getElementById("imageSize").textContent = getImageSize(
		imageData.size
	);
	document.getElementById("imageUploadDate").textContent =
		imageData.upload_date.split("T")[0];
	imageModal.show();
}

function appendImagesToContainer(imagesContainer, imageData) {
	const img = new Image();
	img.src = imageData.url;
	img.classList.add("shadow");
	img.classList.add("cursor_pointer");
	img.addEventListener("click", () => openModal(imageData));
	imagesContainer.appendChild(img);
}

function handlePostUpload(imageData) {
	const loader = document.getElementById("uploadLoader");
	const successLoader = document.getElementById("uploadSuccessAnim");
	const successLoaderDiv = document.getElementById("uploadSuccess");
	const imagesContainer = document.getElementById("imagesContainer");

	loader.style.display = "none";
	successLoaderDiv.style.display = "block";
	successLoader.play();
	clearImage();

	appendImagesToContainer(imagesContainer, imageData);
}

function sendImageToServer() {
	console.log("sending image to server");
	const fileInput = document.getElementById("formFile");
	const file = fileInput.files[0];

	if (file) {
		const loader = document.getElementById("uploadLoader");
		loader.style.display = "block";

		const formData = new FormData();
		formData.append("image", file);

		fetch("/api/upload", {
			method: "POST",
			body: formData,
		})
			.then(async (response) => {
				const data = await response.json();
				console.log(data);
				if (response.status == 500) {
					alert("Failed to upload image. Server Error !!");
					loader.style.display = "none";
				} else {
					handlePostUpload(data.data);
				}
			})
			.catch((error) => {
				console.error("Error:", error);
			});
	} else {
		alert("Please choose an image first.");
	}
}

async function fetchAndDisplayAllImages() {
	try {
		// Get the list of image URLs from the /api/images endpoint
		const response = await fetch("/api/images");
		const imageUrls = await response.json();

		const imagesContainer = document.getElementById("imagesContainer");

		// Loop through the image URLs and display each one
		for (let imageData of imageUrls) {
			appendImagesToContainer(imagesContainer, imageData);
		}
	} catch (error) {
		console.error("Error fetching and displaying images:", error);
	}
}

function downloadImageHandler() {
	console.log("download button clicked");
	const modalImage = document.getElementById("modalImage");
	const imageUrl = modalImage.src;
	const imageName = imageUrl.split("/").pop(); // This will extract the image name from the URL. Modify as needed.

	downloadImage(imageUrl, decodeURIComponent(imageName));
}

function downloadImage(imageUrl, imageName) {
	// Send a request to your Flask backend
	fetch("/api/download-image", {
		method: "POST",
		headers: {
			"Content-Type": "application/json",
		},
		body: JSON.stringify({ url: imageUrl }),
	})
		.then((response) => {
			return response.blob();
		})
		.then((blob) => {
			const a = document.createElement("a");
			a.href = URL.createObjectURL(blob);
			// split imageName on _ and remove the first element
			imageName = imageName.split("_").slice(2).join("_");
			a.download = imageName; // You can provide a dynamic filename if needed
			document.body.appendChild(a);
			a.click();
			document.body.removeChild(a);
		})
		.catch((error) => {
			console.error("Error:", error);
		});
}

function logout() {
	fetch("/api/logout", {
		method: "POST",
		headers: {
			"Content-Type": "application/json",
		},
	})
		.then((response) => {
			return response.json();
		})
		.then((data) => {
			console.log(data);
			window.location.replace("/");
		})
		.catch((error) => {
			console.error("Error:", error);
		});
}

// Call the function to fetch and display images
fetchAndDisplayAllImages();
