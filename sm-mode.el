;; sm-mode.el
;;
;; Mode file to support editing of SM files under Emacs.
;;
;; SM files are State Machine input files.  These files are like
;; standard C files except that they contain SM directives.  The SMG
;; (State Machine Generator) is used to preprocess these C files before
;; normal C-compilation to generate state machine management code.
;;
;; This mode extends the existing CC-mode to support SM directives.
;; SM directives are one-line statements which start with an SM
;; directive keyword in the first position on the line (no preceeding
;; whitespace).  The entire directive is contained on a single line
;; with the exception of the CODE_{ directive which indicates the
;; start of a tagged code block which is terminated with The CODE_}
;; DIRECTIVE.
;;
;; To use this mode, add the following to your .emacs file:
;;     (autoload 'sm-mode "sm-mode" "SM Mode" t)
;;     (setq auto-mode-alist (cons '("*.sm" . sm-mode) auto-mode-alist))
;;
;; The operation of this mode can be controlled by the following:
;;    sm-strict-match variable -- If set and non-nil, this indicates that
;;                                SM directives MUST start at the beginning
;;                                of the line.
;;                                The default is to recognize the SM directive
;;                                keyword anywhere on the line as long as it
;;                                is preceeded only by whitespace.  This will
;;                                allow the SM directive line to be properly
;;                                indented when typed as part of the C code
;;                                flow without requiring repositioning of the
;;                                cursor to the start of the line.
;;                                The disadvantage of not enabling this
;;                                variable is that any line which happens to
;;                                have an SM directive keyword as the first
;;                                non-whitespace character will be interpreted
;;                                as an actual SM directive.
;;
;; This mode adds the following faces:
;;    sm-primary-keyword-face
;;    sm-aux-keyword-face
;;    sm-embed-keyword-face
;;    sm-embed-other-face
;;    sm-tag-face
;;    sm-code-face
;;
;; See the SMG documentation for more information.
;;
;; Copyright 2000 by Kevin Quick
;; All rights reserved.

(require 'custom)

(eval-when-compile
  (require 'cc-defs)
  (require 'cc-engine))

(defcustom sm-strict-match nil
  "Require strict start-of-line SM directive matching.
When set, an SM directive line won't be recognized unless the SM directive
keyword is at the start of the line.  The default is not set, which will
recognized an SM directive line even if the SM directive is preceeded by
whitespace (which will happen during normal code entry)."
  :type 'boolean
  :group 'sm
  :require 'sm-mode)

(defface sm-primary-keyword-face '((((class color))
				    (:background "gray20"
				     :foreground "yellow"))
				   (t (:bold t)))
  "Main State Machine (SM) directive keywords"
  :group 'sm)

(defface sm-aux-keyword-face '((((class color))
				    (:background "gray50"
				     :foreground "yellow"))
				   (t (:bold t)))
  "Auxiliary State Machine (SM) directive keywords"
  :group 'sm)

(defface sm-embed-keyword-face '((((class color))
				  (:background "gray75"))
				 (t (:bold t)))
  "Embedded State Machine (SM) keywords"
  :group 'sm)

(defface sm-embed-other-face '((((class color))
				(:background "gray75")))
  "Miscellaneous embedded State Machine (SM) keywords"
  :group 'sm)

(defface sm-tag-face '((t (:bold t)))
  "Parameter tag on a SM line"
  :group 'sm)

(defface sm-code-face '((((class color))
			 (:background "gray40")))
  "Tagged segment of code --- NOT PRESENTLY USED"
  :group 'sm)

(defface sm-tag-face '((t (:bold t)))
  "Tagged segment of code"
  :group 'sm)

(defvar sm-directive '"sm_directive")
(defvar sm-block-end '"sm_block_end")
(defvar sm-block-predicate '"sm_block_predicate")
(defvar sm-block-start '"sm_block_start")


(progn
  (setq sm-primary-keywords '(("SM_NAME" . sm-directive)
			      ("STATE" . sm-directive)
			      ("INIT_STATE" . sm-directive)
			      ("EVENT" . sm-directive)
			      ("TRANS+" . sm-directive)
			      ("TRANS=" . sm-directive)
			      ("TRANS" . sm-directive)))

  (setq sm-aux-keywords '(("SM_DESC" . sm-directive)
			  ("SM_INCL" . sm-directive)
			  ("ST_DESC" . sm-directive)
			  ("EV_DESC" . sm-directive)
			  ("SM_OBJ" . sm-directive)
			  ("SM_EVT" . sm-directive)
			  ("CODE_}" . sm-block-end)
			  ("CODE_{". sm-block-start)
			  ("CODE_" . sm-block-predicate)
			  ("PROMELA_}" . sm-block-end)
			  ("PROMELA_{". sm-block-start)
			  ("PROMELA_" . sm-block-predicate)
			  ("CODE" . sm-directive)))

  (setq sm-all-keywords (append sm-primary-keywords sm-aux-keywords))
)


(defun sm-fontlock-hook ()
  "Setup hook for SM faces and modes."
  (mapcar (lambda (faceinfo)
	    (setq font-lock-keywords (cons faceinfo
					   font-lock-keywords)))
	  '(
	    ;; Primary Keywords
	    ("^SM_NAME" . sm-primary-keyword-face)
	    ("^STATE"   . sm-primary-keyword-face)
	    ("^INIT_STATE"   . sm-primary-keyword-face)
	    ("^EVENT"   . sm-primary-keyword-face)
	    ("^TRANS="  . sm-primary-keyword-face)
	    ("^TRANS\\+" . sm-primary-keyword-face)
	    ("^\\(TRANS\\) "  . (1 sm-primary-keyword-face))
	    ;; Auxiliary Keywords
	    ("^SM_OBJ"  . sm-aux-keyword-face)
	    ("^SM_EVT"  . sm-aux-keyword-face)
	    ("^SM_DESC" . sm-aux-keyword-face)
	    ("^SM_INCL" . sm-aux-keyword-face)
	    ("^ST_DESC" . sm-aux-keyword-face)
	    ("^EV_DESC" . sm-aux-keyword-face)
	    ("^CODE"    . sm-aux-keyword-face)
	    ("^CODE_{"  . sm-aux-keyword-face)
	    ("^CODE_}"  . sm-aux-keyword-face)
	    ("^PROMELA"    . sm-aux-keyword-face)
	    ("^PROMELA_{"  . sm-aux-keyword-face)
	    ("^PROMELA_}"  . sm-aux-keyword-face)
	    ;; Embedded keywords
	    ("_#OBJ"    . sm-embed-keyword-face)
	    ("_#EVT"    . sm-embed-keyword-face)
	    ("_#[a-zA-Z][a-zA-Z0-9_]*" . sm-embed-other-face)
	    ("_/OBJ"    . sm-embed-keyword-face)
	    ("_/EVT"    . sm-embed-keyword-face)
	    ("_/[a-zA-Z][a-zA-Z0-9_]*" . sm-embed-other-face)
	    ;; Comment face for descriptions
	    ("^##.*"    . font-lock-comment-face)
	    ("^\\(SM_DESC\\|ST_DESC\\|EV_DESC\\)[ \t]+\\(.*\\)" . (2 font-lock-comment-face))
	    ("^STATE[ \t]+[^ \t]+[ \t]+\\(.*\\)" . (1 font-lock-comment-face))
	    ("^INIT_STATE[ \t]+[^ \t]+[ \t]+\\(.*\\)" . (1 font-lock-comment-face))
	    ("^EVENT[ \t]+[^ \t]+[ \t]+[^ \t]+[ \t]+[^ \t]+[ \t]+\\(.*\\)" . (1 font-lock-comment-face))
	    ;; SM line tag words
	    ("^\\(SM_NAME\\|STATE\\|INIT_STATE\\|EVENT\\|CODE\\|CODE_{\\)[ \t]+\\([^ \t\n]+\\)" . (2 sm-tag-face t))
	    ;; SM tagged code
	    ;; kwq: it would be nice to highlight tagged code to distinguish
	    ;;      it from other code, but that doesn't appear to be possible.
	    ;; misc attempts:
	    ;("^CODE_{.+\n\\(.\\|\n\\)*^CODE_}" . (1 sm-code-face t))
	    ;("^CODE_{\\(.*\\)" . (1 sm-code-face t))
	    ;("^CODE_{.*\n\\(.*\n\\)*CODE_}" . (1 sm-code-face t))
	    ;("^CODE_{.*\n\\([^\(CODE_}\)]*\n\\)*CODE_}" . (0 sm-code-face t))
	    ;; The following almost does it, but it highlights from the 
	    ;; FIRST CODE_{ to the LAST CODE_}...
	    ; ("^CODE_{.*\n\\(.*\n\\)*CODE_}" . (0 sm-code-face t))
	    ;; The following works as long as the tagged code doesn't
	    ;; contain a capital C character.
	    ; ("^CODE_{.*\n\\([^C]\\)*CODE_}" . (0 sm-code-face t))
	    ))
)

;;kwq: highlight wildcards and arguments only on directive lines?


(add-hook 'font-lock-mode-hook 'sm-fontlock-hook)

(defun sm-directive-line-p ( &optional directive )
  "Checks the current line to see if it is an SM directive line.  If
the optional argument is specified, it names a directive that is to
be specifically checked for.  Returns t or nil."
  (save-excursion
    (save-restriction
      (let* (word-start word-end word sm-word)
	(widen)
	(beginning-of-line)
	(if (not sm-strict-match) (skip-chars-forward " \t"))
	(setq word-start (point))
	(skip-chars-forward "^ \t\n")
	(setq word-end (point))
	(setq word (buffer-substring word-start word-end))
	(if (setq sm-word (assoc word sm-all-keywords))
	    (if directive
	      (if (equal directive (car sm-word))
		  (cdr sm-word)
		nil)
	      (cdr sm-word))
	  nil)))))


(defun sm-guess-basic-syntax ()
  "Front-end syntax guessing to try to determine the syntax context of
   the SM file at the current point.  Checks for an SM directive line
   and if not found, passes on to the CC-mode syntax checking."
  (save-excursion
    (save-restriction
      (let* (syntax dcheck
	     (real-point -1))
	(beginning-of-line)
	;; Check for one of our SM keywords; if found, that's our syntax
	(if (setq dcheck (sm-directive-line-p))
	    (c-add-syntax dcheck (point))
	  ;; We didn't recognize one of our SM directives.
	  ;; First, check if the previous line was a CODE_{ SM statement,
	  ;; which is the start of a block and therefore the current
	  ;; line should be a statement-block-intro.
	  (save-excursion
	    (let* ((start-point (point)))
	      (forward-line -1)
	      (if (sm-directive-line-p "CODE_{")
		  (c-add-syntax 'statement-block-intro start-point))
	      ;; Now move back even one more to see if THAT is the
	      ;; CODE_{ line.  If so, then the segment above noted a
	      ;; statement-block-intro syntax, and the current line
	      ;; will likely be a statement syntax, but the point for
	      ;; the syntax will incorrectly be the CODE_{ line rather
	      ;; than the statement-block-intro, so the indentation
	      ;; will be computed relative to the wrong position.  We
	      ;; try to find and fix this.
	      (if (not (consp syntax))
		  (progn
		    (save-excursion
		      (c-forward-syntactic-ws)
		      (setq real-point (point)))
		    (forward-line -1)
		    (if (not (sm-directive-line-p "CODE_{"))
			(setq real-point -1))))))
	  ;; We haven't determined any SM-related syntax, so let the
	  ;; CC-mode syntax parser do its thing.
	  (if (not (consp syntax))
	      (progn
		(setq syntax (orig-c-guess-basic-syntax))
		(if (and (> real-point -1) (> (length syntax) 0))
		    (let* ((stmnt (car syntax)))
		      (if (equal 'statement (car stmnt))
			  (progn
			    (setq stmnt (cons 'statement real-point))
			    (setq syntax (append (list stmnt)
						 (cdr syntax))))))))))
;	;; Special fixups: if it's an SM code block delimiter, add the
;	;; block-open or block-close syntax as appropriate.
;	(if (sm-directive-line-p "CODE_{") (c-add-syntax 'block-open))
;	(if (sm-directive-line-p "CODE_}") (c-add-syntax 'block-close))
	;; Now return the syntax we and our CC-mode buddy figured out
	syntax)))
)

(defun sm-electric-brace (arg)
  "Called when an open or close brace is typed in sm-mode.  This function
   is called prior to the c-electric-brace function and suppresses the call
   to the latter if the current syntax is sm-block-predicate to prevent
   the brace from a CODE_{ or CODE_} directive from being forced onto
   its own line."
  (interactive "*P")
  (if c-auto-newline
      (let ((syntax (c-guess-basic-syntax)))
	(if (assq 'sm-block-predicate syntax)
	    (progn
	      (self-insert-command (prefix-numeric-value arg))
	      (c-indent-line)
	      (if (assq 'sm-block-start (c-guess-basic-syntax))
		  (insert-string "  ")
		(newline)
		(c-indent-line)))
	  (c-electric-brace arg)))
    (self-insert-command (prefix-numeric-value arg))))


(defun sm-mode-hook ()
  "Setup hook for SM extension to CC-mode"
  ;; Extend the syntax testing to check for SM directives.
  ;; Unfortunately, c-guess-basic-syntax isn't extensible, so
  ;; push our syntax tester in front of it using that symbol name.
  (if (not (eq (symbol-function 'c-guess-basic-syntax)
	       (symbol-function 'sm-guess-basic-syntax)))
      (progn
	(fset 'orig-c-guess-basic-syntax
	      (symbol-function 'c-guess-basic-syntax))
	(fset 'c-guess-basic-syntax (symbol-function 'sm-guess-basic-syntax))))
  ;; Intercept the c-electric-brace function for SM directives.  We'd prefer
  ;; to use the c-hanging-braces-alist to fix this, but it DOES NOT work for
  ;; some reason and typing "CODE_{" always causes a newline to be inserted
  ;; both before and after the brace (same for "CODE_}", regardless of the
  ;; c-hanging-braces-alist settings.
  (define-key c-mode-base-map "{" 'sm-electric-brace)
  (define-key c-mode-base-map "}" 'sm-electric-brace)
; wish this worked...
;  (setq c-hanging-braces-alist (cons '(sm-block-predicate after)
;				     c-hanging-braces-alist))
  ; Align all SM directives on the left column
  ; Normally this would be done with lines like:
  ;    (c-set-offset 'sm-directive -1000 t)
  ; except that c-set-offset checks to make sure the syntax (the first arg)
  ; matches known syntax elements; since ours are new, we add them by hand.
  ;(c-set-offset sm-directive -1000 t)
  (setq c-offsets-alist (cons (cons 'sm-directive -1000) c-offsets-alist))
  ;(c-set-offset 'sm-block-end -1000 t)
  (setq c-offsets-alist (cons (cons 'sm-block-end -1000) c-offsets-alist))
  ;(c-set-offset 'sm-block-start -1000 t)
  (setq c-offsets-alist (cons (cons 'sm-block-start -1000) c-offsets-alist))
  ;(c-set-offset 'sm-block-predicate -1000 t)
  (setq c-offsets-alist (cons (cons 'sm-block-predicate -1000) c-offsets-alist))
)

; Be sure to add our setup hook to the end so that a user's c-set-style
; doesn't override our c-hanging-braces-alist settings.

(add-hook 'c-mode-common-hook 'sm-mode-hook 1)

(defun sm-mode ()
  "*Mode for State Machine (SM) files.  These are files that are processed by
the SMG utility (see http://smg.sf.net)."
  (interactive 'nil)
  (c-mode)
)

(provide 'sm-mode)
