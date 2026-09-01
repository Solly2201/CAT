import type { QuizQuestion } from "../types";

/**
 * Right to Information questions.
 *
 * Each is answerable from the article it names, and its explanation
 * rests on the same section that article cites. Nothing here asks about
 * fee amounts (set by rules outside the corpus) or about Commissioners'
 * tenure (ss.13/16/27, excluded as pre-2019 text).
 */
export const rightToInformationQuestions: QuizQuestion[] = [
  {
    id: "rti-what-1",
    articleSlug: "what-is-the-right-to-information",
    difficulty: "easy",
    format: "multiple-choice",
    prompt: "Under section 3, who holds the right to information?",
    options: [
      { id: "a", text: "All citizens" },
      { id: "b", text: "Only journalists and researchers" },
      { id: "c", text: "Only a person directly affected by the record" },
      { id: "d", text: "Only registered social organisations" }
    ],
    correctOptionId: "a",
    explanation:
      "Section 3 states that subject to the provisions of the Act, all citizens shall have the right to information. There is no requirement to show a special interest in the subject matter.",
    citation: { sourceId: "rti", unitNumber: "3", label: "Right to Information Act, 2005, Section 3" }
  },
  {
    id: "rti-what-2",
    articleSlug: "what-is-the-right-to-information",
    difficulty: "medium",
    format: "multiple-choice",
    prompt: "An office refuses a request by pointing to the Official Secrets Act, 1923. What does section 22 say about that conflict?",
    options: [
      { id: "a", text: "The older Act prevails over this one" },
      { id: "b", text: "The two Acts apply equally and the office chooses" },
      { id: "c", text: "This Act has effect notwithstanding the Official Secrets Act" },
      { id: "d", text: "The conflict must be referred to a High Court" }
    ],
    correctOptionId: "c",
    explanation:
      "Section 22 gives this Act effect notwithstanding anything inconsistent contained in the Official Secrets Act, 1923, and any other law in force at the time.",
    citation: { sourceId: "rti", unitNumber: "22", label: "Right to Information Act, 2005, Section 22" }
  },
  {
    id: "rti-what-3",
    articleSlug: "what-is-the-right-to-information",
    difficulty: "hard",
    format: "multiple-choice",
    prompt: "The Act does not apply to the intelligence and security organisations in the Second Schedule. What is carved back out of that exclusion?",
    options: [
      { id: "a", text: "Nothing; the exclusion is absolute" },
      { id: "b", text: "Information about allegations of corruption" },
      { id: "c", text: "Any information more than ten years old" },
      { id: "d", text: "Information requested by a Member of Parliament" }
    ],
    correctOptionId: "b",
    explanation:
      "Section 24's first proviso says information pertaining to allegations of corruption is not excluded. Information about alleged human rights violations may also be provided, with the approval of the Central Information Commission.",
    citation: { sourceId: "rti", unitNumber: "24", label: "Right to Information Act, 2005, Section 24" }
  },
  {
    id: "rti-publish-1",
    articleSlug: "what-public-authorities-must-publish",
    difficulty: "easy",
    format: "true-false",
    prompt: "True or false: under section 4, a public authority must keep its records catalogued and indexed in a form that makes the right to information workable.",
    options: [
      { id: "a", text: "True" },
      { id: "b", text: "False" }
    ],
    correctOptionId: "a",
    explanation:
      "Section 4 requires every public authority to maintain its records duly catalogued and indexed in a manner and form that facilitates the right to information under the Act.",
    citation: { sourceId: "rti", unitNumber: "4", label: "Right to Information Act, 2005, Section 4" }
  },
  {
    id: "rti-publish-2",
    articleSlug: "what-public-authorities-must-publish",
    difficulty: "medium",
    format: "multiple-choice",
    prompt: "Which of these must a public authority publish about itself under section 4?",
    options: [
      { id: "a", text: "The home addresses of all its employees" },
      { id: "b", text: "A list of every citizen who has filed a request" },
      { id: "c", text: "The procedure it follows in its decision-making process" },
      { id: "d", text: "Its internal file notings from the previous year" }
    ],
    correctOptionId: "c",
    explanation:
      "Section 4 requires publication of a defined list of particulars, including the organisation's functions and duties, the powers and duties of its officers and employees, and the procedure followed in its decision-making process.",
    citation: { sourceId: "rti", unitNumber: "4", label: "Right to Information Act, 2005, Section 4" }
  },
  {
    id: "rti-publish-3",
    articleSlug: "what-public-authorities-must-publish",
    difficulty: "medium",
    format: "multiple-choice",
    prompt: "What does section 5 require every public authority to do?",
    options: [
      { id: "a", text: "Appoint a lawyer for every applicant" },
      { id: "b", text: "Designate Public Information Officers in its offices" },
      { id: "c", text: "Publish a daily register of visitors" },
      { id: "d", text: "Refer all requests to the Information Commission" }
    ],
    correctOptionId: "b",
    explanation:
      "Section 5 requires every public authority to designate as many officers as Central or State Public Information Officers, in all administrative units or offices, as are necessary to provide information to those requesting it.",
    citation: { sourceId: "rti", unitNumber: "5", label: "Right to Information Act, 2005, Section 5" }
  },
  {
    id: "rti-request-1",
    articleSlug: "how-to-make-an-rti-request",
    difficulty: "easy",
    format: "multiple-choice",
    prompt: "In which languages may an RTI request be made under section 6?",
    options: [
      { id: "a", text: "English only" },
      { id: "b", text: "Hindi only" },
      { id: "c", text: "Any language at all, without restriction" },
      { id: "d", text: "English, Hindi, or the official language of the area" }
    ],
    correctOptionId: "d",
    explanation:
      "Section 6(1) allows a request in writing or through electronic means in English or Hindi or in the official language of the area in which the application is being made.",
    citation: { sourceId: "rti", unitNumber: "6", label: "Right to Information Act, 2005, Section 6" }
  },
  {
    id: "rti-request-2",
    articleSlug: "how-to-make-an-rti-request",
    difficulty: "easy",
    format: "multiple-choice",
    prompt: "An officer asks you to explain why you want a record before accepting your request. What does section 6 say?",
    options: [
      { id: "a", text: "No reason need be given" },
      { id: "b", text: "A written reason is required" },
      { id: "c", text: "A reason is needed only for old records" },
      { id: "d", text: "The reason must be approved by a senior officer" }
    ],
    correctOptionId: "a",
    explanation:
      "Section 6(2) says an applicant shall not be required to give any reason for requesting the information, or any personal details except those necessary to contact them.",
    citation: { sourceId: "rti", unitNumber: "6", label: "Right to Information Act, 2005, Section 6" }
  },
  {
    id: "rti-request-3",
    articleSlug: "how-to-make-an-rti-request",
    difficulty: "hard",
    format: "scenario",
    scenario:
      "Anita sends a request to her district office, but the record is actually held by a different public authority.",
    prompt: "What must the office that received her application do?",
    options: [
      { id: "a", text: "Reject it and ask her to apply again elsewhere" },
      { id: "b", text: "Hold it until the other authority asks for it" },
      { id: "c", text: "Transfer it and inform her, within five days" },
      { id: "d", text: "Forward it to the Information Commission instead" }
    ],
    correctOptionId: "c",
    explanation:
      "Section 6(3) requires the authority to transfer the application, or the appropriate part of it, to the authority concerned and inform the applicant immediately. The proviso requires the transfer as soon as practicable and in no case later than five days.",
    citation: { sourceId: "rti", unitNumber: "6", label: "Right to Information Act, 2005, Section 6" }
  },
  {
    id: "rti-request-4",
    articleSlug: "how-to-make-an-rti-request",
    difficulty: "medium",
    format: "true-false",
    prompt: "True or false: if a person cannot put their request in writing, the Public Information Officer must help put it into writing.",
    options: [
      { id: "a", text: "True" },
      { id: "b", text: "False" }
    ],
    correctOptionId: "a",
    explanation:
      "The proviso to section 6(1) requires the Public Information Officer to render all reasonable assistance to a person making the request orally, to reduce it to writing.",
    citation: { sourceId: "rti", unitNumber: "6", label: "Right to Information Act, 2005, Section 6" }
  },
  {
    id: "rti-time-1",
    articleSlug: "how-long-an-rti-reply-takes",
    difficulty: "easy",
    format: "multiple-choice",
    prompt: "What is the outer time limit in section 7 for disposing of an ordinary request?",
    options: [
      { id: "a", text: "Seven days" },
      { id: "b", text: "Thirty days" },
      { id: "c", text: "Ninety days" },
      { id: "d", text: "One hundred and twenty days" }
    ],
    correctOptionId: "b",
    explanation:
      "Section 7(1) requires the officer to act as expeditiously as possible and in any case within thirty days, either providing the information on payment of the prescribed fee or rejecting the request under sections 8 or 9.",
    citation: { sourceId: "rti", unitNumber: "7", label: "Right to Information Act, 2005, Section 7" }
  },
  {
    id: "rti-time-2",
    articleSlug: "how-long-an-rti-reply-takes",
    difficulty: "medium",
    format: "multiple-choice",
    prompt: "Information sought concerns the life or liberty of a person. Within what time must it be provided?",
    options: [
      { id: "a", text: "The same thirty days" },
      { id: "b", text: "Seven days" },
      { id: "c", text: "Forty-eight hours" },
      { id: "d", text: "Immediately, with no fixed limit stated" }
    ],
    correctOptionId: "c",
    explanation:
      "The proviso to section 7(1) requires information concerning the life or liberty of a person to be provided within forty-eight hours of the receipt of the request.",
    citation: { sourceId: "rti", unitNumber: "7", label: "Right to Information Act, 2005, Section 7" }
  },
  {
    id: "rti-time-3",
    articleSlug: "how-long-an-rti-reply-takes",
    difficulty: "hard",
    format: "multiple-choice",
    prompt: "The officer simply does not reply within the time allowed. How does the Act treat that silence?",
    options: [
      { id: "a", text: "The request lapses and must be filed again" },
      { id: "b", text: "The clock restarts from the date of the reminder" },
      { id: "c", text: "The applicant must wait for an actual decision" },
      { id: "d", text: "The request is deemed to have been refused" }
    ],
    correctOptionId: "d",
    explanation:
      "Section 7(2) deems the request refused where the officer fails to give a decision within the specified period, which is what makes an appeal possible instead of leaving the applicant waiting indefinitely.",
    citation: { sourceId: "rti", unitNumber: "7", label: "Right to Information Act, 2005, Section 7" }
  },
  {
    id: "rti-time-4",
    articleSlug: "how-long-an-rti-reply-takes",
    difficulty: "medium",
    format: "multiple-choice",
    prompt: "A public authority misses the section 7(1) time limit and then supplies the information. What does the Act say about the fee?",
    options: [
      { id: "a", text: "The information must be provided free of charge" },
      { id: "b", text: "A double fee becomes payable" },
      { id: "c", text: "The usual fee still applies" },
      { id: "d", text: "The fee is decided by the appellate authority" }
    ],
    correctOptionId: "a",
    explanation:
      "Section 7(6) requires that the person be provided the information free of charge where the public authority fails to comply with the time limits specified in section 7(1).",
    citation: { sourceId: "rti", unitNumber: "7", label: "Right to Information Act, 2005, Section 7" }
  },
  {
    id: "rti-exempt-1",
    articleSlug: "information-that-can-be-refused",
    difficulty: "medium",
    format: "multiple-choice",
    prompt: "Which of these is a ground listed in section 8 for withholding information?",
    options: [
      { id: "a", text: "The applicant did not explain why they want it" },
      { id: "b", text: "The record is more than five years old" },
      { id: "c", text: "Disclosure would impede an investigation or prosecution" },
      { id: "d", text: "The office considers the request inconvenient" }
    ],
    correctOptionId: "c",
    explanation:
      "Section 8(1)(h) exempts information which would impede the process of investigation or the apprehension or prosecution of offenders. Inconvenience and the applicant's reasons are not grounds at all.",
    citation: { sourceId: "rti", unitNumber: "8", label: "Right to Information Act, 2005, Section 8" }
  },
  {
    id: "rti-exempt-2",
    articleSlug: "information-that-can-be-refused",
    difficulty: "hard",
    format: "multiple-choice",
    prompt: "What can override the exemption for commercial confidence or trade secrets?",
    options: [
      { id: "a", text: "The applicant's consent" },
      { id: "b", text: "A larger public interest in disclosure" },
      { id: "c", text: "The passage of one year" },
      { id: "d", text: "Nothing; that exemption is absolute" }
    ],
    correctOptionId: "b",
    explanation:
      "Section 8(1)(d) allows disclosure of commercial confidence, trade secrets or intellectual property where the competent authority is satisfied that a larger public interest warrants it. The same qualification applies to fiduciary information under clause (e).",
    citation: { sourceId: "rti", unitNumber: "8", label: "Right to Information Act, 2005, Section 8" }
  },
  {
    id: "rti-exempt-3",
    articleSlug: "information-that-can-be-refused",
    difficulty: "medium",
    format: "multiple-choice",
    prompt: "Section 9 adds one ground of rejection outside section 8. What is it?",
    options: [
      { id: "a", text: "The record is held in a foreign language" },
      { id: "b", text: "The applicant has filed too many requests" },
      { id: "c", text: "The file has been sent for archiving" },
      { id: "d", text: "Access would infringe a copyright not belonging to the State" }
    ],
    correctOptionId: "d",
    explanation:
      "Section 9 lets the officer reject a request where providing access would involve infringement of copyright subsisting in a person other than the State.",
    citation: { sourceId: "rti", unitNumber: "9", label: "Right to Information Act, 2005, Section 9" }
  },
  {
    id: "rti-partial-1",
    articleSlug: "partial-access-and-third-party-information",
    difficulty: "medium",
    format: "multiple-choice",
    prompt: "A file contains one exempt paragraph and many pages that are not exempt. What does section 10 require?",
    options: [
      { id: "a", text: "The whole file is withheld" },
      { id: "b", text: "The non-exempt part may be released after severance" },
      { id: "c", text: "The file goes to the Commission for a decision" },
      { id: "d", text: "The applicant must narrow the request and re-apply" }
    ],
    correctOptionId: "b",
    explanation:
      "Section 10(1) allows access to that part of the record which does not contain exempt information and can reasonably be severed from the part that does.",
    citation: { sourceId: "rti", unitNumber: "10", label: "Right to Information Act, 2005, Section 10" }
  },
  {
    id: "rti-partial-2",
    articleSlug: "partial-access-and-third-party-information",
    difficulty: "easy",
    format: "true-false",
    prompt: "True or false: when only part of a record is released, the applicant must be given a notice saying so.",
    options: [
      { id: "a", text: "True" },
      { id: "b", text: "False" }
    ],
    correctOptionId: "a",
    explanation:
      "Section 10(2) requires the officer to give the applicant a notice informing them that only part of the record is being provided, after severance of the exempt material.",
    citation: { sourceId: "rti", unitNumber: "10", label: "Right to Information Act, 2005, Section 10" }
  },
  {
    id: "rti-partial-3",
    articleSlug: "partial-access-and-third-party-information",
    difficulty: "hard",
    format: "multiple-choice",
    prompt: "The record was supplied by a third party who treated it as confidential. What must happen before disclosure?",
    options: [
      { id: "a", text: "The third party must be sued first" },
      { id: "b", text: "The applicant must obtain the third party's signature" },
      { id: "c", text: "Written notice to the third party within five days" },
      { id: "d", text: "Nothing; third-party material is always exempt" }
    ],
    correctOptionId: "c",
    explanation:
      "Section 11 requires the officer, within five days of receiving the request, to give the third party written notice of the request and of the intention to disclose, and to invite that party's submission.",
    citation: { sourceId: "rti", unitNumber: "11", label: "Right to Information Act, 2005, Section 11" }
  },
  {
    id: "rti-appeal-1",
    articleSlug: "appealing-an-rti-refusal",
    difficulty: "easy",
    format: "multiple-choice",
    prompt: "Within what period must a first appeal under section 19 be filed?",
    options: [
      { id: "a", text: "Seven days" },
      { id: "b", text: "Thirty days" },
      { id: "c", text: "Ninety days" },
      { id: "d", text: "There is no time limit" }
    ],
    correctOptionId: "b",
    explanation:
      "Section 19(1) allows an appeal within thirty days from the expiry of the period for a decision, or from receipt of the decision, to an officer senior in rank to the Public Information Officer.",
    citation: { sourceId: "rti", unitNumber: "19", label: "Right to Information Act, 2005, Section 19" }
  },
  {
    id: "rti-appeal-2",
    articleSlug: "appealing-an-rti-refusal",
    difficulty: "medium",
    format: "multiple-choice",
    prompt: "Who hears a second appeal?",
    options: [
      { id: "a", text: "The District Magistrate" },
      { id: "b", text: "The High Court" },
      { id: "c", text: "The head of the same department" },
      { id: "d", text: "The Central or State Information Commission" }
    ],
    correctOptionId: "d",
    explanation:
      "Section 19(3) provides that a second appeal against the first-appeal decision lies with the Central Information Commission or the State Information Commission, within ninety days.",
    citation: { sourceId: "rti", unitNumber: "19", label: "Right to Information Act, 2005, Section 19" }
  },
  {
    id: "rti-appeal-3",
    articleSlug: "appealing-an-rti-refusal",
    difficulty: "hard",
    format: "multiple-choice",
    prompt: "How long does the appellate officer have to dispose of a first appeal?",
    options: [
      { id: "a", text: "Thirty days, extendable to forty-five in total" },
      { id: "b", text: "Ninety days, with no extension" },
      { id: "c", text: "Forty-eight hours" },
      { id: "d", text: "No period is specified" }
    ],
    correctOptionId: "a",
    explanation:
      "Section 19(6) requires disposal within thirty days of receipt, or within an extended period not exceeding forty-five days in total from the date of filing, for reasons to be recorded in writing.",
    citation: { sourceId: "rti", unitNumber: "19", label: "Right to Information Act, 2005, Section 19" }
  },
  {
    id: "rti-appeal-4",
    articleSlug: "appealing-an-rti-refusal",
    difficulty: "medium",
    format: "true-false",
    prompt: "True or false: an appeal filed after thirty days can never be accepted.",
    options: [
      { id: "a", text: "True" },
      { id: "b", text: "False" }
    ],
    correctOptionId: "b",
    explanation:
      "The proviso to section 19(1) lets the appellate officer admit a late appeal if satisfied that the appellant was prevented by sufficient cause from filing in time.",
    citation: { sourceId: "rti", unitNumber: "19", label: "Right to Information Act, 2005, Section 19" }
  },
  {
    id: "rti-penalty-1",
    articleSlug: "complaints-and-penalties-under-rti",
    difficulty: "medium",
    format: "multiple-choice",
    prompt: "What is the daily penalty under section 20, and its ceiling?",
    options: [
      { id: "a", text: "Rs 100 a day, up to Rs 10,000" },
      { id: "b", text: "Rs 250 a day, up to Rs 25,000" },
      { id: "c", text: "Rs 500 a day, with no ceiling" },
      { id: "d", text: "A single fixed fine of Rs 25,000" }
    ],
    correctOptionId: "b",
    explanation:
      "Section 20(1) requires a penalty of two hundred and fifty rupees for each day until the application is received or the information furnished, subject to a total not exceeding twenty-five thousand rupees.",
    citation: { sourceId: "rti", unitNumber: "20", label: "Right to Information Act, 2005, Section 20" }
  },
  {
    id: "rti-penalty-2",
    articleSlug: "complaints-and-penalties-under-rti",
    difficulty: "hard",
    format: "multiple-choice",
    prompt: "In a penalty proceeding under section 20, who must prove that the officer acted reasonably and diligently?",
    options: [
      { id: "a", text: "The officer" },
      { id: "b", text: "The applicant who complained" },
      { id: "c", text: "The public authority's legal adviser" },
      { id: "d", text: "Neither; the Commission decides without evidence" }
    ],
    correctOptionId: "a",
    explanation:
      "The second proviso to section 20(1) places the burden of proving that he or she acted reasonably and diligently on the Public Information Officer. The first proviso also guarantees a reasonable opportunity of being heard.",
    citation: { sourceId: "rti", unitNumber: "20", label: "Right to Information Act, 2005, Section 20" }
  },
  {
    id: "rti-penalty-3",
    articleSlug: "complaints-and-penalties-under-rti",
    difficulty: "medium",
    format: "scenario",
    scenario:
      "Ravi cannot file a request at all: the office has no Public Information Officer, and the assistant refuses to accept his application for forwarding.",
    prompt: "Which route does section 18 give him?",
    options: [
      { id: "a", text: "A civil suit against the office" },
      { id: "b", text: "A complaint to the Information Commission" },
      { id: "c", text: "A writ petition, as the only remedy" },
      { id: "d", text: "Nothing until he has filed a request" }
    ],
    correctOptionId: "b",
    explanation:
      "Section 18 makes it the duty of the Central or State Information Commission to receive and inquire into a complaint from a person unable to submit a request, whether because no officer was appointed or because the assistant officer refused to accept the application.",
    citation: { sourceId: "rti", unitNumber: "18", label: "Right to Information Act, 2005, Section 18" }
  }
];
