# blockbuilding
This codebase was created to test candidate-based blockbuilding and compare it to getBlockTemplate results.

You can read about our proposal in the following gist: https://gist.github.com/murchandamus/5cb413fe9f26dbce57abfd344ebbfaf2#file-candidate-set-based-block-building-md

# FAQ

• What format do the `.mempool` files have?

The `.mempool` file is a simple list of transactions. After a line describing the headers that starts with a pound sign, each line consists of txid, total\_fee weight and ancestors separated by spaces. The ancestors consist of a list of txids also separated by spaces.

Example:

<pre>
# txid total_fee weight ancestor [ancestor... etc]
b79a4e42dd039d84b59ce99658d34497fec81e165e7350e8584e61b4ce1c072e 90000 767
6484a2479bfc8bb75078dfaa5e424935c73d09e0b7285358d10168dac1d28bf5 50000 1028 23b4fad5e06d644abe0d502456b8f32f38dc544db8ab3ec3a2c44c7f7da3ce30 8a80680152befbde49d1ec13d9e7257ea57e2c0f18efc18280bfef92ed42d63d
</pre>

• How does a mempool file get loaded?

When loading the mempool file, we first create transactions from each line and backfill the ancestors as _parents_ and _ancestors_ both. Later, when we backfill the relatives of transactions, we add children and descendants, and remove parents that are also ancestors of parents. This way, the import is agnostic to whether it is provided the full ancestor set, just the parents, or anything in between. The provided ancestors must at least include all parents for a correct transaction graph to result.
