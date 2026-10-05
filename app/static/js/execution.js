// Interactive Execution Runner & AI Troubleshooter

document.addEventListener('DOMContentLoaded', function () {
    const executionContainer = document.getElementById('execution-runner');
    if (!executionContainer) return;

    const executionId = executionContainer.getAttribute('data-execution-id');
    const nextStepBtn = document.getElementById('btn-next-step');
    const completeBtn = document.getElementById('btn-complete-execution');

    // Next step button
    if (nextStepBtn) {
        nextStepBtn.addEventListener('click', async function () {
            nextStepBtn.disabled = true;
            nextStepBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Advancing...';

            try {
                const res = await apiRequest(`/api/executions/${executionId}/next`, {
                    method: 'POST'
                });

                if (res.success) {
                    showToast('Step completed successfully', 'success');
                    // Reload page to reflect next active step and updated progress
                    window.location.reload();
                } else {
                    throw new Error(res.message || 'Failed to advance step');
                }
            } catch (err) {
                showToast(err.message, 'danger');
                nextStepBtn.disabled = false;
                nextStepBtn.innerHTML = '<i class="bi bi-arrow-right me-1"></i> Next Step';
            }
        });
    }

    // Complete Execution button
    if (completeBtn) {
        completeBtn.addEventListener('click', async function () {
            completeBtn.disabled = true;
            completeBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Completing...';

            try {
                const res = await apiRequest(`/api/executions/${executionId}/complete`, {
                    method: 'POST'
                });

                if (res.success) {
                    showToast('Execution marked as completed!', 'success');
                    window.location.reload();
                } else {
                    throw new Error(res.message || 'Failed to complete execution');
                }
            } catch (err) {
                showToast(err.message, 'danger');
                completeBtn.disabled = false;
                completeBtn.innerHTML = '<i class="bi bi-check2-circle me-1"></i> Finish Execution';
            }
        });
    }

    // ==========================================
    // GROQ AI STEP TROUBLESHOOTER
    // ==========================================
    const troubleshootModalEl = document.getElementById('groqAiTroubleshootModal');
    const btnAskAi = document.getElementById('btn-troubleshoot-step');
    const btnSubmitTroubleshoot = document.getElementById('btn-submit-troubleshoot');
    const observationInput = document.getElementById('troubleshoot-observation');
    const aiResponseArea = document.getElementById('troubleshoot-ai-response');
    const aiResponseContent = document.getElementById('troubleshoot-ai-content');
    const troubleshootSpinner = document.getElementById('troubleshoot-spinner');

    if (btnSubmitTroubleshoot) {
        btnSubmitTroubleshoot.addEventListener('click', async function () {
            const stepTitle = executionContainer.getAttribute('data-step-title') || '';
            const instructions = executionContainer.getAttribute('data-step-instructions') || '';
            const expected = executionContainer.getAttribute('data-step-expected') || '';
            const observation = observationInput.value.trim();

            if (!observation) {
                showToast('Please describe the error or paste the command output.', 'warning');
                return;
            }

            troubleshootSpinner.classList.remove('d-none');
            aiResponseArea.classList.add('d-none');
            btnSubmitTroubleshoot.disabled = true;

            try {
                const res = await apiRequest('/api/ai/troubleshoot', {
                    method: 'POST',
                    body: {
                        stepTitle: stepTitle,
                        instructions: instructions,
                        expectedOutcome: expected,
                        observation: observation
                    }
                });

                if (res.success && res.advice) {
                    aiResponseContent.innerText = res.advice;
                    aiResponseArea.classList.remove('d-none');
                } else {
                    throw new Error(res.message || 'Unable to retrieve AI advice');
                }
            } catch (err) {
                showToast(err.message, 'danger');
            } finally {
                troubleshootSpinner.classList.add('d-none');
                btnSubmitTroubleshoot.disabled = false;
            }
        });
    }
});
