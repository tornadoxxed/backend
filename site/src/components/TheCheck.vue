<script setup></script>

<script>
import doxxed from "../assets/doxxed.json";
import Web3Modal from "web3modal";
import Web3 from "web3";

const DUNE_KEY = import.meta.env.VITE_DUNE_KEY;

const QUERY_WORKING = ["QUERY_STATE_PENDING", "QUERY_STATE_EXECUTING"];
const QUERY_DONE = "QUERY_STATE_COMPLETED";

export default {
  created() {
    const providerOptions = {};

    this.web3Modal = new Web3Modal({
      cacheProvider: true,
      disableInjectedProvider: false,
      providerOptions,
    });
    if (this.web3Modal.cachedProvider) {
      this.connect();
    }
  },
  methods: {
    async connect() {
      const provider = await this.web3Modal.connect();

      // Subscribe to accounts change
      provider.on("accountsChanged", this.accountChanged);

      // Subscribe to provider connection
      provider.on("connect", () => {
        this.accountChanged();
        this.connected = true;
      });

      // Subscribe to provider disconnection
      provider.on("disconnect", () => {
        this.logout();
      });

      provider.autoRefreshOnNetworkChange = false;
      this.web3 = new Web3(provider);
      this.accountChanged();
      this.connected = true;
    },
    accountChanged() {
      if (this.web3) {
        this.web3.eth.getAccounts().then((accounts) => {
          const [coinbase] = accounts;
          this.address = coinbase;
          this.getDuneQuery(1279881, { entry: this.address });
        });
      }
    },
    logout() {
      this.web3Modal.clearCachedProvider();
      this.connected = false;
      this.address = "";
      this.tcUses = null;
    },
    search() {
      if (this.searchString !== "") {
        this.address = "";
        this.getDuneQuery(1279881, { entry: this.searchString });
      }
    },
    async getDuneQuery(queryId, queryParameters) {
      this.loading = true;
      this.tcUses = null;
      const executionId = await this.executeDuneQuery(queryId, queryParameters);
      await this.waitForDuneQuery(executionId);
    },
    async executeDuneQuery(queryId, queryParameters) {
      const executeResponse = await fetch(
        `https://api.dune.com/api/v1/query/${queryId}/execute`,
        {
          method: "POST",
          headers: {
            Accept: "application/json",
            "Content-Type": "application/json",
            "x-dune-api-key": DUNE_KEY,
          },
          body: JSON.stringify({
            query_parameters: queryParameters,
          }),
        }
      );
      const execute = await executeResponse.json();
      const executionId = execute.execution_id;
      return executionId;
    },
    async waitForDuneQuery(executionId) {
      fetch(`https://api.dune.com/api/v1/execution/${executionId}/status`, {
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
          "x-dune-api-key": DUNE_KEY,
        },
      }).then((response) => {
        response.json().then((waiting) => {
          const state = waiting.state;

          if (QUERY_WORKING.includes(state)) {
            setTimeout(this.waitForDuneQuery, 3000, executionId);
          } else if (state != QUERY_DONE) {
            console.error(`Error: Query state is ${state}`);
          } else {
            this.getDuneQueryData(executionId);
          }
        });
      });
    },
    async getDuneQueryData(executionId) {
      const response = await fetch(
        `https://api.dune.com/api/v1/execution/${executionId}/results`,
        {
          headers: {
            Accept: "application/json",
            "Content-Type": "application/json",
            "x-dune-api-key": DUNE_KEY,
          },
        }
      );
      const responseJ = await response.json();

      this.tcUses = responseJ.result.rows;
      this.loading = false;

      this.address = this.tcUses[0].address;
    },
  },

  data() {
    return {
      searchString: "",
      doxxed: doxxed,
      web3Modal: {},
      connected: false,
      web3: {},
      address: "",
      tcUses: null,
      loading: false,
    };
  },
  computed: {
    filteredDoxxed() {
      const filteredDoxxed =
        this.address === ""
          ? this.doxxed
          : this.doxxed.filter(
              (wo) =>
                Object.values(wo)
                  .join("")
                  .toLowerCase()
                  .indexOf(this.address.toLowerCase()) !== -1
            );
      return filteredDoxxed;
    },
  },
};
</script>

<template>
  <div class="centered">
    <button v-if="!connected" raised @click="connect">Connect Wallet</button>
    <button v-if="connected" raised @click="logout">Logout</button>
    <span v-if="!connected">
      <input
        class="address"
        v-model="searchString"
        v-on:keyup.enter="search"
        placeholder="Address or ENS"
      />
      <button raised @click="search">Search</button>
    </span>
    <span v-else>{{ address }}</span>
    <p v-if="loading">LOADING...</p>
  </div>
  <div v-if="filteredDoxxed.length == 1">
    <h2>⚠️Your privacy might be at risk⚠️</h2>
    <p>Potential Link caused by matching total cross-pool amounts</p>
    <table>
      <thead>
        <th>Depositor</th>
        <th>Recipient</th>
        <th>0.1 ETH</th>
        <th>1 ETH</th>
        <th>10 ETH</th>
        <th>100 ETH</th>
      </thead>
      <tbody>
        <tr v-for="address in filteredDoxxed">
          <td>
            <a
              :href="'https://blockscan.com/address/' + address.depositor_list"
              target="_blank"
              >{{ address.depositor_list }}</a
            >
          </td>
          <td>
            <a
              :href="'https://blockscan.com/address/' + address.recipient_list"
              target="_blank"
              >{{ address.recipient_list }}</a
            >
          </td>
          <td>{{ address["0.1 ETH"] }}</td>
          <td>{{ address["1 ETH"] }}</td>
          <td>{{ address["10 ETH"] }}</td>
          <td>{{ address["100 ETH"] }}</td>
        </tr>
      </tbody>
    </table>
  </div>
  <div class="uses-tc" v-if="tcUses && tcUses.length > 0">
    <p>This address has been involved in Tornado Cash transactions</p>
    <table>
      <thead>
        <th>Blockchain</th>
        <!--<th>Address</th>-->
        <th>ENS</th>
        <th>Pool</th>
        <th>Deposits</th>
        <th>Withdrawals</th>
        <th>First Seen</th>
        <th>Last Seen</th>
      </thead>
      <tbody>
        <tr v-for="pool in tcUses">
          <td>{{ pool.blockchain }}</td>
          <!--<td>{{ pool.address }}</td>-->
          <td>
            <span v-if="JSON.parse(pool.ens_list).length > 0">
              <ul v-for="ens in JSON.parse(pool.ens_list)">
                <li>{{ ens }}</li>
              </ul>
            </span>
          </td>
          <td>{{ pool.pool }}</td>
          <td>{{ pool.total_deposits }}</td>
          <td>{{ pool.total_withdraws }}</td>
          <td>{{ pool.first_seen }}</td>
          <td>{{ pool.last_seen }}</td>
        </tr>
      </tbody>
    </table>
    <br />
    <p>
      The following graph shows if the same account was used to deposit and
      withdraw, clearing the balance each time
    </p>
    <iframe
      :src="
        'https://dune.com/embeds/1279928/2193729/7ff67d30-522c-48d9-afe2-ff3a6955e51a?wallet_address=' +
        address
      "
      height="500"
      width="1000"
      title="chart 1"
    ></iframe>
  </div>
  <div v-if="tcUses && tcUses.length == 0">
    This address has not been involved in Tornado Cash transactions
  </div>
</template>

<style>
table,
tr,
td,
th {
  border: #68ffb8 1px solid;
  padding: 3px;
}
h2 {
  text-align: center;
  font-size: 2em;
  margin: 20px;
}
iframe {
  margin: 10px;
  background: white;
}
.address {
  margin-left: 5px;
}
.centered {
  text-align: center;
}
.uses-tc {
  margin: 30px;
}
.elipsis {
  max-width: 250px;
  text-overflow: ellipsis;
}
</style>
