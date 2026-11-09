document.addEventListener("DOMContentLoaded", () => {
    // DOM Elements
    const file1Input = document.getElementById("input-1");
    const file2Input = document.getElementById("input-2");
    const drop1 = document.getElementById("drop-1");
    const drop2 = document.getElementById("drop-2");
    const prompt1 = document.getElementById("prompt-1");
    const prompt2 = document.getElementById("prompt-2");
    const previewBox1 = document.getElementById("preview-box-1");
    const previewBox2 = document.getElementById("preview-box-2");
    const previewImg1 = document.getElementById("preview-img-1");
    const previewImg2 = document.getElementById("preview-img-2");
    const card1 = document.getElementById("card-1");
    const card2 = document.getElementById("card-2");
    const reset1 = document.getElementById("reset-1");
    const reset2 = document.getElementById("reset-2");

    const compareForm = document.getElementById("compare-form");
    const btnCompare = document.getElementById("btn-compare");
    const btnQuickSample = document.getElementById("btn-quick-sample");
    const errorAlert = document.getElementById("error-alert");
    const errorMessage = document.getElementById("error-message");
    const resultsSection = document.getElementById("results-section");

    // Results Elements
    const winnerTitleText = document.getElementById("winner-title-text");
    const winnerSubText = document.getElementById("winner-sub-text");
    const scoreNum1 = document.getElementById("score-num-1");
    const scoreNum2 = document.getElementById("score-num-2");
    const score10Num1 = document.getElementById("score-10-num-1");
    const score10Num2 = document.getElementById("score-10-num-2");
    const scoreThumb1 = document.getElementById("score-thumb-1");
    const scoreThumb2 = document.getElementById("score-thumb-2");
    const tierTag1 = document.getElementById("tier-tag-1");
    const tierTag2 = document.getElementById("tier-tag-2");
    const diffBadgeText = document.getElementById("diff-badge-text");
    const scorecard1 = document.getElementById("scorecard-1");
    const scorecard2 = document.getElementById("scorecard-2");
    const winnerPill1 = document.getElementById("winner-pill-1");
    const winnerPill2 = document.getElementById("winner-pill-2");

    const annotatedView1 = document.getElementById("annotated-view-1");
    const annotatedView2 = document.getElementById("annotated-view-2");
    const toggleLandmarks = document.getElementById("toggle-landmarks");
    const breakdownList = document.getElementById("breakdown-list");
    const summaryText = document.getElementById("summary-text");

    let originalImg1Url = "";
    let originalImg2Url = "";
    let annotatedImg1Url = "";
    let annotatedImg2Url = "";
    let radarChartInstance = null;

    // --- FILE HANDLING & PREVIEW ---
    function setupDropZone(dropZone, fileInput, promptEl, previewBox, previewImg, cardEl, isFirst) {
        // Click to open file picker
        dropZone.addEventListener("click", () => fileInput.click());

        // Drag & Drop
        ["dragenter", "dragover"].forEach(evt => {
            dropZone.addEventListener(evt, (e) => {
                e.preventDefault();
                e.stopPropagation();
                dropZone.classList.add("dragover");
            });
        });

        ["dragleave", "drop"].forEach(evt => {
            dropZone.addEventListener(evt, (e) => {
                e.preventDefault();
                e.stopPropagation();
                dropZone.classList.remove("dragover");
            });
        });

        dropZone.addEventListener("drop", (e) => {
            if (e.dataTransfer.files && e.dataTransfer.files[0]) {
                fileInput.files = e.dataTransfer.files;
                handleFileSelect(fileInput.files[0], promptEl, previewBox, previewImg, cardEl, isFirst);
            }
        });

        fileInput.addEventListener("change", () => {
            if (fileInput.files && fileInput.files[0]) {
                handleFileSelect(fileInput.files[0], promptEl, previewBox, previewImg, cardEl, isFirst);
            }
        });
    }

    function handleFileSelect(file, promptEl, previewBox, previewImg, cardEl, isFirst) {
        if (!file.type.startsWith("image/")) {
            showError("Vui lòng chỉ tải lên tệp hình ảnh (JPG, PNG, WEBP).");
            return;
        }
        hideError();
        const reader = new FileReader();
        reader.onload = (e) => {
            previewImg.src = e.target.result;
            promptEl.style.display = "none";
            previewBox.style.display = "flex";
            cardEl.classList.add("has-file");
            if (isFirst) {
                originalImg1Url = e.target.result;
            } else {
                originalImg2Url = e.target.result;
            }
        };
        reader.readAsDataURL(file);
    }

    setupDropZone(drop1, file1Input, prompt1, previewBox1, previewImg1, card1, true);
    setupDropZone(drop2, file2Input, prompt2, previewBox2, previewImg2, card2, false);

    // Reset Buttons
    reset1.addEventListener("click", (e) => {
        e.stopPropagation();
        file1Input.value = "";
        previewImg1.src = "";
        prompt1.style.display = "block";
        previewBox1.style.display = "none";
        card1.classList.remove("has-file");
        originalImg1Url = "";
    });

    reset2.addEventListener("click", (e) => {
        e.stopPropagation();
        file2Input.value = "";
        previewImg2.src = "";
        prompt2.style.display = "block";
        previewBox2.style.display = "none";
        card2.classList.remove("has-file");
        originalImg2Url = "";
    });

    // --- QUICK SAMPLE COMPARE ---
    btnQuickSample.addEventListener("click", async () => {
        hideError();
        setLoading(true);

        // Preload preview images
        previewImg1.src = "/static/images/sample1.jpg";
        previewImg2.src = "/static/images/sample2.jpg";
        originalImg1Url = "/static/images/sample1.jpg";
        originalImg2Url = "/static/images/sample2.jpg";
        prompt1.style.display = "none";
        prompt2.style.display = "none";
        previewBox1.style.display = "flex";
        previewBox2.style.display = "flex";
        card1.classList.add("has-file");
        card2.classList.add("has-file");

        try {
            const resp = await fetch("/api/compare-samples", { method: "POST" });
            const result = await resp.json();
            if (!result.success) {
                showError(result.error || "Không thể tải ảnh mẫu.");
                setLoading(false);
                return;
            }
            displayResults(result);
        } catch (err) {
            showError("Lỗi kết nối khi gọi so sánh ảnh mẫu: " + err.message);
        } finally {
            setLoading(false);
        }
    });

    // --- FORM SUBMIT COMPARE ---
    compareForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        hideError();

        // Check if both files are selected
        const f1 = file1Input.files[0];
        const f2 = file2Input.files[0];

        if (!f1 && !originalImg1Url) {
            showError("Vui lòng chọn hoặc kéo thả Ứng viên 1 (Ảnh 1).");
            return;
        }
        if (!f2 && !originalImg2Url) {
            showError("Vui lòng chọn hoặc kéo thả Ứng viên 2 (Ảnh 2).");
            return;
        }

        // If files are user uploads
        if (f1 && f2) {
            setLoading(true);
            const formData = new FormData();
            formData.append("file1", f1);
            formData.append("file2", f2);

            try {
                const resp = await fetch("/api/compare", {
                    method: "POST",
                    body: formData,
                });
                const result = await resp.json();
                if (!result.success) {
                    showError(result.error || "Không thể hoàn thành so sánh.");
                    setLoading(false);
                    return;
                }
                displayResults(result);
            } catch (err) {
                showError("Lỗi đường truyền hoặc máy chủ: " + err.message);
            } finally {
                setLoading(false);
            }
        } else {
            // Re-run sample or existing
            btnQuickSample.click();
        }
    });

    // --- DISPLAY RESULTS ---
    function displayResults(payload) {
        const data = payload.data;
        annotatedImg1Url = payload.annotated1;
        annotatedImg2Url = payload.annotated2;

        // Set Images
        scoreThumb1.src = originalImg1Url;
        scoreThumb2.src = originalImg2Url;

        annotatedView1.src = toggleLandmarks.checked ? annotatedImg1Url : originalImg1Url;
        annotatedView2.src = toggleLandmarks.checked ? annotatedImg2Url : originalImg2Url;

        // Banner & Winner Info
        winnerTitleText.textContent = data.winner_text;
        winnerSubText.textContent = data.winner_sub;
        diffBadgeText.textContent = `Cách biệt: +${data.diff_overall}đ`;

        // Scoreboard Card 1
        scoreNum1.textContent = data.score1;
        score10Num1.textContent = data.scale10_1;
        tierTag1.textContent = data.tier1.badge;

        // Scoreboard Card 2
        scoreNum2.textContent = data.score2;
        score10Num2.textContent = data.scale10_2;
        tierTag2.textContent = data.tier2.badge;

        // Winner Highlights
        scorecard1.classList.remove("is-winner");
        scorecard2.classList.remove("is-winner");
        winnerPill1.style.display = "none";
        winnerPill2.style.display = "none";

        if (data.overall_winner === 1) {
            scorecard1.classList.add("is-winner");
            winnerPill1.style.display = "block";
        } else if (data.overall_winner === 2) {
            scorecard2.classList.add("is-winner");
            winnerPill2.style.display = "block";
        }

        // Render Breakdown List
        renderBreakdownList(data.comparisons);

        // Render Radar Chart
        renderRadarChart(data.comparisons);

        // Render Summary
        summaryText.innerHTML = formatMarkdown(data.summary);

        // Show Section & Scroll
        resultsSection.style.display = "block";
        setTimeout(() => {
            resultsSection.scrollIntoView({ behavior: "smooth", block: "start" });
        }, 150);
    }

    // Toggle Landmarks wireframe
    toggleLandmarks.addEventListener("change", () => {
        if (toggleLandmarks.checked) {
            annotatedView1.src = annotatedImg1Url;
            annotatedView2.src = annotatedImg2Url;
        } else {
            annotatedView1.src = originalImg1Url;
            annotatedView2.src = originalImg2Url;
        }
    });

    // Render Breakdown Cards
    function renderBreakdownList(comparisons) {
        breakdownList.innerHTML = "";
        comparisons.forEach((item, idx) => {
            let pillClass = "pill-tie";
            let pillText = `<i class="fa-solid fa-handshake"></i> Ngang nhau`;

            if (item.winner === 1) {
                pillClass = "pill-winner-1";
                pillText = `<i class="fa-solid fa-trophy"></i> Ảnh 1 thắng (+${item.diff}đ)`;
            } else if (item.winner === 2) {
                pillClass = "pill-winner-2";
                pillText = `<i class="fa-solid fa-trophy"></i> Ảnh 2 thắng (+${item.diff}đ)`;
            }

            const card = document.createElement("div");
            card.className = "crit-item-card";
            card.innerHTML = `
                <div class="crit-header">
                    <div class="crit-title-group">
                        <h4>${idx + 1}. ${item.name} <span class="crit-weight">(Trọng số: ${item.weight})</span></h4>
                    </div>
                    <span class="crit-winner-pill ${pillClass}">${pillText}</span>
                </div>
                <div class="crit-bars-grid">
                    <div class="crit-bar-col">
                        <div class="crit-bar-label">
                            <span style="color: var(--c1-primary);">Ứng viên 1: <strong>${item.score1}/100</strong></span>
                        </div>
                        <div class="crit-bar-track">
                            <div class="crit-bar-fill-1" style="width: ${item.score1}%;"></div>
                        </div>
                        <div class="crit-metrics-detail">${item.detail1}</div>
                    </div>
                    <div class="crit-bar-col">
                        <div class="crit-bar-label">
                            <span style="color: var(--c2-primary);">Ứng viên 2: <strong>${item.score2}/100</strong></span>
                        </div>
                        <div class="crit-bar-track">
                            <div class="crit-bar-fill-2" style="width: ${item.score2}%;"></div>
                        </div>
                        <div class="crit-metrics-detail">${item.detail2}</div>
                    </div>
                </div>
                <div class="crit-verdict-box">
                    <i class="fa-solid fa-circle-check" style="color: #38bdf8; margin-right: 6px;"></i>
                    <strong>Đánh giá so sánh:</strong> ${item.verdict}
                    <div class="crit-ideal-note">
                        <i class="fa-solid fa-ruler-combined" style="margin-right: 4px;"></i> Chuẩn thế giới: ${item.ideal}
                    </div>
                </div>
            `;
            breakdownList.appendChild(card);
        });
    }

    // Render Radar Chart
    function renderRadarChart(comparisons) {
        const labels = comparisons.map(c => c.name.split("(")[0].trim());
        const data1 = comparisons.map(c => c.score1);
        const data2 = comparisons.map(c => c.score2);

        const ctx = document.getElementById("radar-chart").getContext("2d");
        if (radarChartInstance) {
            radarChartInstance.destroy();
        }

        radarChartInstance = new Chart(ctx, {
            type: "radar",
            data: {
                labels: labels,
                datasets: [
                    {
                        label: "Ứng viên 1 (Ảnh 1)",
                        data: data1,
                        backgroundColor: "rgba(0, 210, 255, 0.25)",
                        borderColor: "#00d2ff",
                        borderWidth: 2.5,
                        pointBackgroundColor: "#00d2ff",
                        pointBorderColor: "#fff",
                        pointHoverBackgroundColor: "#fff",
                        pointHoverBorderColor: "#00d2ff",
                    },
                    {
                        label: "Ứng viên 2 (Ảnh 2)",
                        data: data2,
                        backgroundColor: "rgba(236, 72, 153, 0.25)",
                        borderColor: "#ec4899",
                        borderWidth: 2.5,
                        pointBackgroundColor: "#ec4899",
                        pointBorderColor: "#fff",
                        pointHoverBackgroundColor: "#fff",
                        pointHoverBorderColor: "#ec4899",
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    r: {
                        angleLines: { color: "rgba(255, 255, 255, 0.12)" },
                        grid: { color: "rgba(255, 255, 255, 0.08)" },
                        pointLabels: {
                            color: "#cbd5e1",
                            font: { size: 11, weight: "600", family: "Plus Jakarta Sans" }
                        },
                        ticks: {
                            backdropColor: "transparent",
                            color: "#64748b",
                            stepSize: 20,
                            beginAtZero: false,
                            min: 40,
                            max: 100
                        }
                    }
                },
                plugins: {
                    legend: {
                        labels: {
                            color: "#f1f5f9",
                            font: { size: 13, weight: "700" }
                        }
                    }
                }
            }
        });
    }

    // Helper functions
    function setLoading(isLoading) {
        btnCompare.disabled = isLoading;
        btnQuickSample.disabled = isLoading;
        const btnText = btnCompare.querySelector(".btn-text");
        const btnLoading = btnCompare.querySelector(".btn-loading");

        if (isLoading) {
            btnText.style.display = "none";
            btnLoading.style.display = "inline-flex";
        } else {
            btnText.style.display = "inline-flex";
            btnLoading.style.display = "none";
        }
    }

    function showError(msg) {
        errorMessage.textContent = msg;
        errorAlert.style.display = "flex";
        errorAlert.scrollIntoView({ behavior: "smooth", block: "center" });
    }

    function hideError() {
        errorAlert.style.display = "none";
    }

    function formatMarkdown(text) {
        if (!text) return "";
        let formatted = text
            .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
            .replace(/\*(.*?)\*/g, "<em>$1</em>")
            .replace(/\n\n/g, "<br><br>")
            .replace(/• (.*?)(<br>|$)/g, "<div style='margin-bottom: 8px;'><i class='fa-solid fa-angle-right' style='color:#38bdf8; margin-right:6px;'></i>$1</div>");
        return formatted;
    }
});
