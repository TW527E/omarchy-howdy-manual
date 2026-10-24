#define _DEFAULT_SOURCE
#include <security/pam_modules.h>
#include <security/pam_ext.h>
#include <stdlib.h>
#include <string.h>

PAM_EXTERN int pam_sm_authenticate(pam_handle_t *pamh, int flags,
                                   int argc, const char **argv) {
    (void)flags; (void)argc; (void)argv;
    char *response = NULL;
    /* Always ask, even if a caller supplied an empty authentication token. */
    int result = pam_prompt(pamh, PAM_PROMPT_ECHO_OFF, &response,
        "Password (or press Enter for face recognition): ");
    if (result == PAM_SUCCESS && response) {
        int choice = response[0] ? PAM_IGNORE : PAM_SUCCESS;
        result = pam_set_item(pamh, PAM_AUTHTOK, response);
        if (result == PAM_SUCCESS) result = choice;
    } else if (result == PAM_SUCCESS) {
        result = PAM_CONV_ERR;
    }
    if (response) {
        explicit_bzero(response, strlen(response));
        free(response);
    }
    return result;
}

PAM_EXTERN int pam_sm_setcred(pam_handle_t *pamh, int flags,
                             int argc, const char **argv) {
    (void)pamh; (void)flags; (void)argc; (void)argv;
    return PAM_SUCCESS;
}
