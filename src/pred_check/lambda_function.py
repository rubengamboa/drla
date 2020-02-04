import json
from urllib.parse import parse_qs
import base64
import traceback
import pred_check.PredicateProofChecker as PredChecker


def get_arg(event, args, name):
    arg = ""
    if name in event:
        arg = event[name]
    elif name in args:
        arg = " ".join(args[name])
    return arg


def lambda_handler(event, _context):
    # noinspection PyBroadException,PyBroadException
    try:
        args = {}
        if "body" in event:
            body = event["body"]
            if "isBase64Encoded" in event and event["isBase64Encoded"]:
                body = base64.b64decode(body).decode("utf-8")
            args = parse_qs(body)
        proof_script = get_arg(event, args, "proof")
        goal = get_arg(event, args, "goal")

        proof = PredChecker.PredicateProof(goal)
        errors = proof.check_proof(proof_script)

        return {
            'statusCode': 200,
            'body': json.dumps({"goal": goal,
                                "proof": proof_script,
                                "errors": errors})
        }
    except Exception:
        return {
            'statusCode': 500,
            'body': json.dumps({"exception": traceback.format_exc()})
        }
