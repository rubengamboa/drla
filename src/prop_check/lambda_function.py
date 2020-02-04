import json
from urllib.parse import parse_qs
import base64
import traceback
import prop_check.PropositionalProofChecker as ppc

def get_arg(event, args, name):
    arg = ""
    if name in event:
        arg = event[name]
    elif name in args:
        arg = " ".join(args[name])
    return arg

def lambda_handler(event, context):
    try:
        args = {}
        body = ""
        if "body" in event:
            body = event["body"]
            if "isBase64Encoded" in event and event["isBase64Encoded"]:
                body = base64.b64decode(body).decode("utf-8")
            args = parse_qs(body)
        proof_script = get_arg(event, args, "proof")
        lhs = get_arg(event, args, "lhs")
        rhs = get_arg(event, args, "rhs")
        extra_axioms = get_arg(event, args, "extra_axioms")
    
        proof = ppc.PropositionalProof(lhs, rhs, extra_axioms)
        errors = proof.check_proof(proof_script)
    
        return {
            'statusCode': 200,
            'body': json.dumps({"lhs":lhs,
                                "rhs":rhs,
                                "extra_axioms":extra_axioms,
                                "proof":proof_script,
                                "errors":errors})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({"exception": traceback.format_exc()})
        }
