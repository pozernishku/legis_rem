"""Tag document text using regex patterns.
"""
import re
import logging


class PatternTagger(object):
    """A pattern-based tagger for document text.

Use by passing a string to the tag() method.

Attributes:
re: Patterns applied when tagging.
tests: An iterable giving pairs of text and expected tags.
"""
    
    re = {
        'start_block': re.compile('^\s*Testifying on (.*):', re.M),
        'end_block': re.compile('^\s*$', re.M),
        'tag': re.compile('^[^,]*, (.*)$', re.M),
    }
    tests = [
        {
            'desc': 'Basic example',
            'text': r"""
            Meeting Transcript

            Testifying on HF2540:
            Representative Sanders
            Mr. Sean Ostrow, FanDuel, Inc.
            Mr. Jake Grassel, Citizens Against Gambling Expansion

            [End]
            """,
            'tags': ['FanDuel, Inc.', 'Citizens Against Gambling Expansion']
        },
    ]

    def __init__(self):
        pass

    def tag(self, text):
        """Tag text.

    Applies a simple parser iterating once over lines of text, with the following rules:
    1. A block (a span of consecutive lines) begins with a line matching the 'start_block' pattern.
    2. A block ends after a line that matches the 'end_block' pattern.
    3. Tags can exist only inside a block.
    4. A tag is a subset of a line inside a block matching the 'tag' pattern.

    :param text: A string of text.
    :return: An iterable of tag text and indexes (the integers that slice the string giving the tag text).
    """

        tags = []
        in_block = False
        offset = 0
        lines = text.split('\n')
        for i, line in enumerate(lines):
            if self.re['start_block'].search(line):
                # Invariant: This line starts a block
                in_block = True
                logging.debug('[start_block]'.format(i))
            logging.debug('{}: {}'.format(i, line))
            if in_block:
                tag_match = self.re['tag'].search(line)
                if tag_match:
                    # Invariant: this line contains a tag
                    logging.debug('[tag]'.format(i))
                    tags.append({
                        'text': tag_match.group(1),
                        'span': [idx + offset for idx in tag_match.regs[1]]
                    })
                    assert text[tags[-1]['span'][0]:tags[-1]['span'][1]] == tag_match.group(1)
                if self.re['end_block'].search(line):
                    # Invariant: this line ends a block
                    in_block = False
                    logging.debug('[end_block]'.format(i))
            offset += len(line) + 1
        return tags

    def test(self, verbose=False):
        print('Testing {}:'.format(self.__class__))
        for case in self.tests:
            tags = self.tag(case['text'])
            if [tag['text'] for tag in tags] == case['tags']:
                print('✓ {}'.format(case['desc']))
            else:
                print('✗ {}'.format(case['desc']))
                print('Result: {}'.format(tags))
                print('Expected: {}'.format(case['tags']))
                if verbose:
                    print('Text:\n{}'.format(case['text']))
                
                
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
    PatternTagger().test()
